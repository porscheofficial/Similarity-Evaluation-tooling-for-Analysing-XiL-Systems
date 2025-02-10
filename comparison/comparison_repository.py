
import asyncio
from logging import getLogger
from PySide6 import QtWidgets as w
from PySide6.QtCore import Signal, QObject, QThread
import PySide6.QtAsyncio as QtAsyncio

from comparison.comparison_result import ComparisonResult

import numpy as np
import pandas as pd
import os
import hashlib
import json

from comparison.metrics.metric_result import MetricResult
from comparison.metrics.signal_data import SignalData
from measurement.channel.channel_data_repository import ChannelDataRepository


class ComparisonRepository(QObject):
    """
    The ComparisonRepository is responsible for storing all ComparisonResults.
    As a comparison is done, its result can be stored using it, such that it is written in persistent storage 
    and can be retrieved at a later stage.
    Each ComparisonResult is identified by its name, therefore the name must be unique, and saving a comparison
    with the same name again will overwrite the previously saved one.
    """
    loadingDone = Signal(ComparisonResult)
    listUpdated = Signal()
    initialized = False

    def __new__(cls) -> 'ComparisonRepository':
        if not hasattr(cls, 'instance'):
            cls.instance = super(ComparisonRepository, cls).__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        if not self.initialized:
            super().__init__()
            self.initialized = True
            self.comparisons = {}
            self.comparison_names = []
            self.logger = getLogger(__name__)
            self.base_path = f"{os.getcwd()}/comparisons"
            self.save_worker = None
            self.load_worker = None
            self._load()

    def save_comparison(self, comparison: ComparisonResult, sync: bool = False):
        if self.save_worker is not None:
            self.logger.warning("Already saving a comparison")
            return

        if comparison.name in self.comparison_names:
            self.logger.error(
                f"Comparison with name {comparison.name} already exists, overwriting it")
        else:
            self.comparison_names.append(comparison.name)
            self.listUpdated.emit()
        self.comparisons[comparison.name] = comparison
        self.save_worker = ComparisonSaveWorker(comparison, self.base_path)
        self.save_worker.done.connect(self.handle_saving_done)
        if sync:
            self.save_worker.run()
        else:
            self.save_worker.start()

    def handle_saving_done(self):
        self.save_worker.quit()
        self.save_worker.wait()
        self.save_worker.deleteLater()
        self.save_worker = None
        self.logger.info("Saving done")

    def load_comparison(self, name: str) -> ComparisonResult:
        """
        This function is meant to be used by the UI only. It does not consistently return the desired comparison if it
        needs to be loaded from persistent storage. Furthermore, the comparison is opened in the GUI automatically if this function is used. If a comparison should be loaded and returned directly, use get_comparison_sync.
        """
        if name not in self.comparison_names:
            self.logger.error(f"Could not find comparison {name}")
            return None

        if name in self.comparisons:
            self.logger.info(f"Comparison {name} already cached")
            self.loadingDone.emit(self.comparisons[name])
            return self.comparisons[name]

        self.logger.info(f"Comparison not cached, loading comparison {name}")

        if self.load_worker is not None:
            self.logger.warning("Already loading a comparison, waiting")
            self.load_worker.wait()
            return None

        self.load_worker = ComparisonLoadWorker(name, self.base_path)
        self.load_worker.done.connect(self.handle_loading_done)
        self.load_worker.start()

    def get_comparison_sync(self, name: str) -> ComparisonResult:
        """
        Gets a comparison from the loaded comparisons or from persistent storage.
        If it is loaded from persistent storage, the execution of this function takes over 5 seconds.
        """
        if name not in self.comparison_names:
            self.logger.error(f"Could not find comparison {name}")
            return None

        if name in self.comparisons:
            self.logger.info(f"Comparison {name} already cached")
            return self.comparisons[name]

        self.logger.info(f"Comparison not cached, loading comparison {name}")

        comparison = None

        def callback(result: ComparisonResult):
            nonlocal comparison
            comparison = result

        worker = ComparisonLoadWorker(name, self.base_path)
        worker.done.connect(callback)
        worker.run()
        worker.wait(5000)
        return comparison

    def handle_loading_done(self, comparison: ComparisonResult):
        self.comparisons[comparison.name] = comparison
        self.comparison_names.append(comparison.name)
        self.load_worker.quit()
        self.load_worker.wait()
        self.load_worker.deleteLater()
        self.load_worker = None
        self.logger.info(f"Loading of {comparison.name} done")
        self.loadingDone.emit(comparison)

    def _load(self):
        if not os.path.exists(self.base_path):
            self.logger.info(
                f"Base Path {self.base_path} does not exist yet. Creating it now")
            os.mkdir(self.base_path)

        comparison_names = []

        for _, _, files in os.walk(self.base_path):
            for filename in files:
                if filename.endswith("_overview.json"):
                    json_data = json.load(open(f"{self.base_path}/{filename}"))
                    comparison_names.append(json_data["name"])

        self.logger.info(f"Found {len(comparison_names)} comparisons")
        self.comparison_names = comparison_names

    def first_measurement(self, comparison: str):
        if comparison not in self.comparison_names:
            self.logger.error(f"Could not find comparison {comparison}")
            return None
        part = comparison.split("-")
        return part[0].strip()

    def second_measurement(self, comparison: str):
        if comparison not in self.comparison_names:
            self.logger.error(f"Could not find comparison {comparison}")
            return None

        part = comparison.split("-")
        part = part[1].split("(")
        return part[0].strip()

    def metric_used(self, comparison: str):
        if comparison not in self.comparison_names:
            self.logger.error(f"Could not find comparison {comparison}")
            return None

        part = "(".join(comparison.split("(")[1:])
        part = ")".join(part.split(")")[:-1])
        return part.strip()

    def remove_comparison(self, name: str):
        if name not in self.comparison_names:
            self.logger.error(f"Could not find comparison {name}")
            return

        self.comparison_names.remove(name)
        if name in self.comparisons:
            self.comparisons.pop(name)

        id = hashlib.sha256(name.encode()).hexdigest()
        channel_results_filename = f"{self.base_path}/{id}_channel_results.parquet"
        overall_result_filename = f"{self.base_path}/{id}_overall_result.parquet"
        channel_id_pairs_filename = f"{self.base_path}/{id}_channel_id_pairs.json"
        overview_filename = f"{self.base_path}/{id}_overview.json"

        os.remove(channel_results_filename)
        os.remove(overall_result_filename)
        os.remove(channel_id_pairs_filename)
        os.remove(overview_filename)

        self.listUpdated.emit()


class ComparisonLoadWorker(QThread):
    done = Signal(ComparisonResult)

    def __init__(self, name: str, base_path: str):
        super().__init__()
        self.name = name
        self.logger = getLogger(__name__)
        self.base_path = base_path
        self.repository = ChannelDataRepository()

    def run(self) -> None:
        self.logger.info(f"Loading comparison {self.name}")

        id = hashlib.sha256(self.name.encode()).hexdigest()
        channel_results_filename = f"{self.base_path}/{id}_channel_results.parquet"
        overall_result_filename = f"{self.base_path}/{id}_overall_result.parquet"
        channel_id_pairs_filename = f"{self.base_path}/{id}_channel_id_pairs.json"

        channel_results = pd.read_parquet(channel_results_filename)
        overall_result = pd.read_parquet(overall_result_filename)
        channel_id_pairs = json.load(open(channel_id_pairs_filename, "r"))
        channel_id_pairs = channel_id_pairs["channel_id_pairs"]

        comparison = ComparisonResult(self.name)

        result_metadata_keys = {}
        input_metadata_keys = {}

        for column in channel_results.columns:
            if column.endswith("values"):
                continue
            if "result_metadata" in column:
                if not column.endswith("timestamps"):
                    self.logger.error(f"Unexpected column {column}")
                    continue
                key = column.split(" ")[-2]
                channel = column.split(" ")[0] + " " + column.split(" ")[1]
                if channel not in result_metadata_keys:
                    result_metadata_keys[channel] = []
                result_metadata_keys[channel].append(key)
            elif "input_metadata" in column:
                if not column.endswith("timestamps"):
                    self.logger.error(f"Unexpected column {column}")
                    continue
                key = column.split(" ")[-2]
                channel = column.split(" ")[0] + " " + column.split(" ")[1]
                if channel not in input_metadata_keys:
                    input_metadata_keys[channel] = []
                input_metadata_keys[channel].append(key)

        for i, (ref_id, eval_id) in enumerate(channel_id_pairs):

            if (i * 100 // len(channel_id_pairs)) != ((i - 1) * 100 // len(channel_id_pairs)):
                self.logger.info(
                    f"Loading comparison {(i * 100) // len(channel_id_pairs)}%")

            ref_channel = self.repository.load(ref_id)
            eval_channel = self.repository.load(eval_id)
            channel_result_value = channel_results[f"{ref_id} {eval_id} values"].to_numpy(
            )
            channel_result_timestamps = channel_results[f"{ref_id} {eval_id} timestamps"].to_numpy(
            )
            channel_result_value = channel_result_value[~np.isnan(
                channel_result_value)]
            channel_result_timestamps = channel_result_timestamps[~np.isnan(
                channel_result_timestamps)]

            channel_result = SignalData(
                channel_result_timestamps, channel_result_value)
            result_metadata = {}
            input_metadata = {}

            if f"{ref_id} {eval_id}" not in result_metadata_keys:
                result_metadata_keys[f"{ref_id} {eval_id}"] = []
            if f"{ref_id} {eval_id}" not in input_metadata_keys:
                input_metadata_keys[f"{ref_id} {eval_id}"] = []

            result_metadata_keys_for_channel = result_metadata_keys[f"{ref_id} {eval_id}"]
            input_metadata_keys_for_channel = input_metadata_keys[f"{ref_id} {eval_id}"]

            for key in result_metadata_keys_for_channel:
                timestamps = channel_results[f"{ref_id} {eval_id} result_metadata {key} timestamps"].to_numpy(
                )
                values = channel_results[f"{ref_id} {eval_id} result_metadata {key} values"].to_numpy(
                )
                timestamps = timestamps[~np.isnan(timestamps)]
                values = values[~np.isnan(values)]
                result_metadata[key] = SignalData(timestamps, values)

            for key in input_metadata_keys_for_channel:
                timestamps = channel_results[f"{ref_id} {eval_id} input_metadata {key} timestamps"].to_numpy(
                )
                values = channel_results[f"{ref_id} {eval_id} input_metadata {key} values"].to_numpy(
                )
                timestamps = timestamps[~np.isnan(timestamps)]
                values = values[~np.isnan(values)]
                input_metadata[key] = SignalData(timestamps, values)

            metric_result = MetricResult(SignalData.from_channel_data(ref_channel), SignalData.from_channel_data(
                eval_channel), channel_result, result_metadata, input_metadata)
            comparison.add_result(ref_channel, eval_channel, metric_result)

        overall_result_value = overall_result["values"]
        overall_result_timestamps = overall_result["timestamps"]
        comparison.result = SignalData(
            overall_result_timestamps, overall_result_value)

        self.logger.info(f"Loaded comparison {self.name}")

        self.done.emit(comparison)


class ComparisonSaveWorker(QThread):
    done = Signal()

    def __init__(self, comparison: ComparisonResult, base_path: str):
        super().__init__()
        self.comparison = comparison
        self.logger = getLogger(__name__)
        self.base_path = base_path

    def run(self) -> None:
        self.logger.info(f"Saving comparison {self.comparison}")

        id = hashlib.sha256(self.comparison.name.encode()).hexdigest()

        channel_results_filename = f"{self.base_path}/{id}_channel_results.parquet"
        overall_result_filename = f"{self.base_path}/{id}_overall_result.parquet"
        channel_id_pairs_filename = f"{self.base_path}/{id}_channel_id_pairs.json"
        overview_filename = f"{self.base_path}/{id}_overview.json"

        channel_results = self.comparison.channel_results

        channel_id_pairs = [[ref_channel.id, eval_channel.id]
                            for ref_channel, eval_channel, _ in channel_results]
        channel_id_pairs_data = {
            "channel_id_pairs": channel_id_pairs
        }
        json.dump(channel_id_pairs_data, open(channel_id_pairs_filename, "w"))
        self.logger.info(
            f"Saved channel id pairs to {channel_id_pairs_filename}")
        dataframe_data: dict[str, np.ndarray] = {}
        for i, (ref_ch, eval_ch, result) in enumerate(channel_results):
            if (i * 100 // len(channel_results)) != ((i - 1) * 100 // len(channel_results)):
                self.logger.info(
                    f"Saving channel results {i * 100 // len(channel_results)}%")

            channel_dataframe = {
                f"{ref_ch.id} {eval_ch.id} values": result.result.values,
                f"{ref_ch.id} {eval_ch.id} timestamps": result.result.timestamps
            }

            for key, value in result.result_metadata.items():
                channel_dataframe[f"{ref_ch.id} {eval_ch.id} result_metadata {key} values"] = value.values
                channel_dataframe[f"{ref_ch.id} {eval_ch.id} result_metadata {key} timestamps"] = value.timestamps

            for key, value in result.input_metadata.items():
                channel_dataframe[f"{ref_ch.id} {eval_ch.id} input_metadata {key} values"] = value.values
                channel_dataframe[f"{ref_ch.id} {eval_ch.id} input_metadata {key} timestamps"] = value.timestamps

            dataframe_data.update(channel_dataframe)

        longest_dataframe_data = max([len(data)
                                     for data in dataframe_data.values()])

        for key in dataframe_data:
            if len(dataframe_data[key]) < longest_dataframe_data:
                data = dataframe_data[key]
                pad_length = longest_dataframe_data - len(dataframe_data[key])

                if data.dtype != np.float64:
                    data = data.astype(np.float64)

                dataframe_data[key] = np.pad(
                    data, (0, pad_length), "constant", constant_values=np.nan)

        dataframe = pd.DataFrame(dataframe_data)
        dataframe.to_parquet(channel_results_filename)

        overall_result = {
            "values": self.comparison.result.values,
            "timestamps": self.comparison.result.timestamps
        }
        pd.DataFrame(overall_result).to_parquet(overall_result_filename)

        overview = {
            "name": self.comparison.name,
        }
        json.dump(overview, open(overview_filename, "w"))

        self.logger.info(f"Saved comparison!")

        self.done.emit()
