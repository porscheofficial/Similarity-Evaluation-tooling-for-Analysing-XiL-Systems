from logging import getLogger
import numpy as np

from comparison.comparison import Comparison
from comparison.metrics.signal_data import SignalData
from comparison.sync_block import SyncBlock
from measurement.channel.channel_data import ChannelData
import math

import itertools


class SyncProcessor:

    def __init__(self) -> None:
        self.logger = getLogger(__name__)

    def find_sync_time(self, channel_data: ChannelData, sync_value: float, after_time: float = 0) -> float:
        """
        Find the time when the channel data reaches a specific value.

        The time is found by interpolating between the timestamps and values of the channel data.

        Parameters
        ----------
        channel_data : ChannelData
            Channel data to find the sync time in.
        sync_value : float
            Value to find the sync time for.

        Returns
        -------
        float
            Time when the channel data reaches the sync value.
        """
        timestamps = channel_data.timestamps()
        values = channel_data.datapoints()
        last_value = values[0]
        tolerance = max(0.1 * np.abs(sync_value), 0.1)
        for i in range(1, len(timestamps)):
            if timestamps[i] <= after_time:
                last_value = values[i]
                continue
            if values[i] >= sync_value and last_value <= sync_value and abs(values[i] - sync_value) < tolerance:
                return timestamps[i]
            if values[i] <= sync_value and last_value >= sync_value and abs(values[i] - sync_value) < tolerance:
                return timestamps[i]
            if values[i] == sync_value:
                return timestamps[i]
            last_value = values[i]
        return timestamps[-1]

    def find_longest_end_sync_time(self, ref_start: float, eval_start: float, comparison: Comparison) -> tuple[float, float]:
        """
        Finds the longest end sync time between the reference measurement and the evaluation measurement.

        Args:
            comparison (Comparison): The comparison object containing the measurements.

        Returns:
            tuple[float, float]: A tuple containing the reference sync end time and the evaluation sync end time.
        """
        ref_length = comparison.ref_measurement.length
        eval_length = comparison.eval_measurement.length
        ref_time = ref_length - ref_start
        eval_time = eval_length - eval_start
        sync_time = min(ref_time, eval_time)
        ref_sync_end = ref_start + sync_time
        eval_sync_end = eval_start + sync_time
        return ref_sync_end, eval_sync_end

    def sync(self, comparison: Comparison, ref_channel: ChannelData, eval_channel: ChannelData, ref_sync_value: float, eval_sync_value: float):
        """
        Synchronizes two channel data streams by finding corresponding sync points and creating sync blocks.
        This method identifies synchronization points in both reference and evaluation channels based on 
        specified sync values, and creates a new sync block. If previous sync blocks exist, it also adjusts 
        the end time of the last sync block.
        Args:
            comparison (Comparison): The comparison object containing sync blocks and other comparison data.
            ref_channel (ChannelData): Reference channel data stream.
            eval_channel (ChannelData): Evaluation channel data stream.
            ref_sync_value (float): The sync value to search for in the reference channel.
            eval_sync_value (float): The sync value to search for in the evaluation channel.
        Returns:
            None: The method modifies the comparison object in-place by adding a new sync block.
        Note:
            - If previous sync blocks exist, the method starts searching for new sync points after the last sync block.
            - The end times of sync blocks are determined to maximize the synchronized period while maintaining 
              temporal alignment between channels.
        """
        ref_sync_after = 0
        eval_sync_after = 0
        if len(comparison.sync_blocks) > 0:
            ref_sync_after = comparison.sync_blocks[-1].ref_start
            eval_sync_after = comparison.sync_blocks[-1].eval_start

        ref_sync_start = self.find_sync_time(ref_channel, ref_sync_value, ref_sync_after)
        eval_sync_start = self.find_sync_time(eval_channel, eval_sync_value, eval_sync_after)
        ref_sync_end, eval_sync_end = self.find_longest_end_sync_time(ref_sync_start, eval_sync_start,
                                                                      comparison)

        sync_block = SyncBlock(ref_sync_start, ref_sync_end,
                               eval_sync_start, eval_sync_end)

        if len(comparison.sync_blocks) > 0:
            min_sync_time = min(ref_sync_start - ref_sync_after, eval_sync_start - eval_sync_after)
            last_sync_block = comparison.sync_blocks[-1]
            comparison.sync_blocks[-1].ref_end = last_sync_block.ref_start + min_sync_time
            comparison.sync_blocks[-1].eval_end = last_sync_block.eval_start + min_sync_time

        comparison.add_sync_block(sync_block)

    def find_all_sync_times(self, channel: ChannelData, use_initial_value: bool) -> list[tuple[float, float]]:
        """
        Finds all the sync times in the given channel.

        Args:
            channel (ChannelData): The channel to search for sync times.

        Returns:
            list[tuple[float, float]]: A list of tuples representing the sync times found in the channel.
                Each tuple contains a timestamp and its corresponding value.

        """
        timestamps = channel.timestamps()
        values = channel.datapoints()
        sync_times = [(timestamps[0], values[0])] if use_initial_value else []
        for i in range(1, len(timestamps)):
            if not math.isclose(values[i], values[i-1]):
                sync_times.append((timestamps[i], values[i]))
        if sync_times[-1] != (timestamps[-1], values[-1]):
            sync_times.append((timestamps[-1], values[-1]))
        return sync_times

    def sync_multi(self, comparison: Comparison, ref_channel: ChannelData, eval_channel: ChannelData, use_initial_value: bool = False):
        """
        Synchronizes multiple segments of data between a reference channel and an evaluation channel.

        This method identifies synchronization markers in both the reference and evaluation channels,
        compares them, and creates synchronization blocks that map segments of the reference channel
        to corresponding segments in the evaluation channel. The synchronization blocks are then added
        to the comparison object.

        Parameters:
        - comparison (Comparison): The comparison object to which synchronization blocks will be added.
        - ref_channel (ChannelData): The reference channel data containing timestamps and datapoints.
        - eval_channel (ChannelData): The evaluation channel data containing timestamps and datapoints.

        Requirements:
        - The number of synchronization markers in the reference and evaluation channels must match.
        - The values of the synchronization markers in the reference and evaluation channels must be close.
        - The end time of a synchronization block must not be before its start time.

        Returns:
        - None

        Raises:
        - Logs an error if the number of synchronization markers in the reference and evaluation channels do not match.
        - Logs an error if the values of the synchronization markers in the reference and evaluation channels do not match.
        - Logs a warning if the end time of a synchronization block is before its start time and skips the block.

        Example:
        >>> processor = SyncProcessor()
        >>> comparison = Comparison()
        >>> ref_channel = ChannelData(timestamps=[0, 1, 2, 3, 4], datapoints=[10, 20, 10, 20, 10])
        >>> eval_channel = ChannelData(timestamps=[0, 1, 2, 3, 4], datapoints=[10, 20, 10, 20, 10])
        >>> processor.sync_multi(comparison, ref_channel, eval_channel)
        >>> # This will add synchronization blocks to the comparison object based on the sync markers.
        """
        ref_sync_markers = self.find_all_sync_times(
            ref_channel, use_initial_value)
        eval_sync_markers = self.find_all_sync_times(
            eval_channel, use_initial_value)
        ref_sync_values = [value for _, value in ref_sync_markers]
        eval_sync_values = [value for _, value in eval_sync_markers]

        if len(ref_sync_values) != len(eval_sync_values):
            self.logger.error(
                "The number of sync markers in the reference and evaluation channel data do not match.")
            return

        for i, ref_sync_value in enumerate(ref_sync_values):
            eval_sync_value = eval_sync_values[i]
            if not math.isclose(ref_sync_value, eval_sync_value):
                self.logger.error(
                    f"The sync markers in the reference and evaluation channel data do not match. index: {i}, ref: {ref_sync_value}, eval: {eval_sync_value}")
                return

        iterator = zip(itertools.pairwise(ref_sync_markers),
                       itertools.pairwise(eval_sync_markers))

        for (ref_prev, ref_next), (eval_prev, eval_next) in iterator:
            ref_start = ref_prev[0]
            ref_end = ref_next[0]
            eval_start = eval_prev[0]
            eval_end = eval_start + (ref_end - ref_start)

            if eval_end > comparison.eval_measurement.length:
                diff = eval_end - comparison.eval_measurement.length
                eval_end -= diff
                ref_end -= diff
                if ref_end < ref_start:
                    self.logger.warning(
                        "The sync block end time is before the start time. The sync block is skipped. ref_start: {}, ref_end: {}, eval_start: {}, eval_end: {}".format(ref_start, ref_end, eval_start, eval_end))
                    continue

            sync_block = SyncBlock(ref_start, ref_end, eval_start, eval_end)
            comparison.add_sync_block(sync_block)
