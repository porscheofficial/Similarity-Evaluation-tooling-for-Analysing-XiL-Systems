

from dataclasses import dataclass
from logging import getLogger
import os
from PySide6.QtCore import QObject, Slot, QThreadPool, QRunnable, QSemaphore, QMetaType
from PySide6.QtCore import Signal as QSignal
from asammdf import MDF, Signal

from comparison.metrics.iso_metric_small import IsoMetricSmall
from comparison.metrics.signal_data import SignalData
from measurement.channel.channel_processor import ChannelProcessor

from .channel.channel_data_repository import ChannelDataRepository
from .channel.channel_repository import ChannelRepository
from .channel.channel import Channel
from .channel.channel_data import ChannelData
from .measurement import Measurement
import uuid

import numpy as np
import math

from more_itertools import chunked


@dataclass
class MeasurementImportInfo():
    filename: str
    remove_constant_channels: bool
    merge_signals: bool
    name_mapping: dict[str, str]
    sample_rate: float


class MeasurementImporter(QObject):
    measurementImported = QSignal(Measurement)

    def __init__(self, info: MeasurementImportInfo):
        super().__init__()
        self.logger = getLogger(__name__)
        self.info = info
        self.measurement = None
        self.chunks_to_process = 0
        self.channel_processor = ChannelProcessor()
        self.channel_repo = ChannelRepository()
        self.data_repo = ChannelDataRepository()

    @Slot()
    def import_measurement(self):
        info = self.info
        self.logger.info(f"Importing measurement from {info.filename}")
        if not os.path.exists(info.filename):
            self.logger.error(f"File {info.filename} does not exist")
            raise OSError(f"File {info.filename} does not exist")

        measurement_id = str(uuid.uuid4())
        self.measurement = Measurement(
            measurement_id, os.path.basename(info.filename), 0, self.info.sample_rate, [])

        mdf = MDF(info.filename)

        last_timestamps = [signal.timestamps[-1]
                           for signal in mdf.iter_channels()]
        self.measurement.length = max(last_timestamps)
        signal_count = len(last_timestamps)
        self.logger.info(f"Measurement length: {self.measurement.length}")

        result_tuples = []
        self.logger.info("Importing signals")

        for i, signal_tuple in enumerate(zip(mdf.iter_channels(), mdf.iter_channels(raw=True))):
            if i % 100 == 0:
                self.logger.info(
                    f"Imported {(i / signal_count)*100:.1f}% of the signals ({i+1})")
            result_tuple = self.process_signal_tuple(signal_tuple)
            if result_tuple is not None:
                result_tuples.append(result_tuple)

        if self.info.merge_signals:
            self.logger.info("Done importing signals, combining duplicates")
            result_tuples = self.combine_duplicates(result_tuples)
            self.logger.info("Done combining duplicates")
        else:
            self.logger.info(
                "Done importing signals, skipping duplicate combination")
        self.logger.info("Saving channels")
        chunk_size = 500

        for i, chunk in enumerate(chunked(result_tuples, chunk_size)):
            self.logger.info(
                f"Processing, {((i+1) / (len(result_tuples)/chunk_size))*100:.1f}% of the chunks ({i+1})")
            self.save_chunk(chunk)

        self.logger.info("Everything done")
        self.measurementImported.emit(self.measurement)
        return self.measurement

    def combine_duplicates(self, result_tuples: list[tuple[Channel, ChannelData]]):
        new_result_tuples: list[tuple[Channel, ChannelData]] = []
        metric = IsoMetricSmall(0.2)
        threshold = 0.999

        # make sure all names are qualified
        for i, (channel, channel_data) in enumerate(result_tuples):
            if not self.channel_repo.is_name_qualified(channel):
                self.logger.error(
                    f"Channel {channel.name} is not qualified, skipping")
                continue
            new_result_tuples.append((channel, channel_data))

        result_tuples = new_result_tuples
        new_result_tuples = []

        for i, (channel, channel_data) in enumerate(result_tuples):
            if i % 100 == 0:
                self.logger.info(
                    f"Processing {(i / len(result_tuples))*100:.1f}% of the channels ({i+1})")
            found_duplicate = False
            signal_name = self.channel_repo.get_signal_name(channel)
            for i, (other, other_data) in enumerate(new_result_tuples):
                other_signal_name = self.channel_repo.get_signal_name(other)
                if signal_name == other_signal_name:
                    result = metric(SignalData.from_channel_data(
                        channel_data), SignalData.from_channel_data(other_data))
                    if result.result.mean() > threshold:
                        self.logger.debug(
                            f"Duplicate channel {channel.name} merged")
                        new_result_tuples[i][0].aliases.append(channel.name)
                        found_duplicate = True
                        break
                    else:
                        self.logger.info(
                            f"Duplicate candidate {signal_name} not merged")
            if not found_duplicate:
                new_result_tuples.append((channel, channel_data))

        return new_result_tuples

    def save_chunk(self, chunk: list[tuple[Channel, ChannelData]]):
        group_id = self.channel_repo.generate_group_id()
        for channel, channel_data in chunk:
            id = self.channel_repo.generate_channel_id(group_id)
            channel.id = id
            channel_data.id = id

            self.measurement.channels.append(channel)

        self.channel_repo.store_group(
            group_id, [channel for channel, _ in chunk])
        self.data_repo.store_group(
            group_id, [channel_data for _, channel_data in chunk])

    def process_signal_tuple(self, signal_tuple: tuple[Signal, Signal]) -> tuple[Channel, ChannelData]:
        signal = signal_tuple[0]
        raw_signal = signal_tuple[1]
        values = signal.samples
        timestamps = signal.timestamps
        raw_values = raw_signal.samples
        raw_values = raw_values.astype(np.float64)
        name = signal.name
        id = "TEMPORARY ID"

        if len(values) == 0:
            self.logger.warning(f"Signal {signal.name} has no values")
            return None

        if len(values) != len(timestamps):
            self.logger.error(
                f"Signal {signal.name} has different number of values and timestamps")
            return None

        if values.dtype in [np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64, np.float16, np.float32, np.float64]:
            values = values.astype(np.float64)
            raw_values = values

        unique_value_names, indices = np.unique(values, return_index=True)

        if len(unique_value_names) == 1:
            self.logger.debug(
                f"Signal {name} is constant, with value {unique_value_names[0]}")
            if self.info.remove_constant_channels:
                self.logger.debug(
                    f"Skipping constant channel {name}")
                return None

        value_mapping = {}
        if len(unique_value_names) <= 20:
            unique_values = raw_values[indices]
            unique_values = [float(value) for value in unique_values]
            value_mapping = dict(zip(unique_values, unique_value_names))

        if len(self.info.name_mapping.items()) != 0:
            if name in self.info.name_mapping:
                name = self.info.name_mapping[name]
            elif name in self.info.name_mapping.values():
                name = name
            else:
                # self.logger.warning(
                #    f"Channel {name} not in name mapping, skipping")
                return None

        channel_data = ChannelData(timestamps, raw_values, name, id)
        channel_data = self.channel_processor.normalize_channel(
            channel_data, self.measurement.length, self.info.sample_rate)
        channel = Channel(id, name, [name],
                          value_name_mapping=value_mapping)

        return channel, channel_data


class ChunkImporter():

    def __init__(self, chunk: list[tuple[Signal, Signal]], length: float, sample_rate: float, skip_constant_channels):
        super().__init__()
        self.chunk = chunk
        self.logger = getLogger(__name__)
        self.logger.info(
            f"Creating worker for chunk with {len(chunk)} signals")
        self.channel_data_repo = ChannelDataRepository()
        self.channel_repo = ChannelRepository()
        self.channel_processor = ChannelProcessor()
        self.length = length
        self.sample_rate = sample_rate
        self.skip_constant_channels = skip_constant_channels

    def run(self):
        self.logger.info(f"Processing chunk")
        channels = []
        channel_datas = []
        group_id = self.channel_repo.generate_group_id()
        for signal, raw_signal in self.chunk:
            values = signal.samples
            timestamps = signal.timestamps
            raw_values = raw_signal.samples
            raw_values = raw_values.astype(np.float64)
            name = signal.name
            id = self.channel_repo.generate_channel_id(group_id)

            if len(values) == 0:
                self.logger.warning(f"Signal {signal.name} has no values")
                continue

            if len(values) != len(timestamps):
                self.logger.error(
                    f"Signal {signal.name} has different number of values and timestamps")
                continue

            if values.dtype in [np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64, np.float16, np.float32, np.float64]:
                values = values.astype(np.float64)
                raw_values = values

            unique_value_names, indices = np.unique(values, return_index=True)

            if len(unique_value_names) == 1:
                self.logger.warning(
                    f"Signal {name} is constant, with value {unique_value_names[0]}")
                if self.skip_constant_channels:
                    self.logger.info(
                        f"Skipping constant channel {name}")
                    continue

            value_mapping = {}
            if len(unique_value_names) <= 20:
                unique_values = raw_values[indices]
                unique_values = [float(value) for value in unique_values]
                value_mapping = dict(zip(unique_values, unique_value_names))

            channel_data = ChannelData(timestamps, raw_values, name, id)
            channel_data = self.channel_processor.normalize_channel(
                channel_data, self.length, self.sample_rate)
            channel = Channel(id, name, [name],
                              value_name_mapping=value_mapping)

            channel_datas.append(channel_data)
            channels.append(channel)

        self.logger.info(f"Done processing chunk, saving...")
        self.channel_data_repo.store_group(group_id, channel_datas)
        self.channel_repo.store_group(group_id, channels)

        return channels, channel_datas
