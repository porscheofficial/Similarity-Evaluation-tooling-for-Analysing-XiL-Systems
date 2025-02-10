import logging
from comparison.sync_block import SyncBlock
from measurement.channel.channel import Channel
from measurement.measurement import Measurement
from .metrics import Metric


class Comparison():
    def __init__(self,  ref_measurement: Measurement, eval_measurement: Measurement):
        """
        Initializes a Comparison object.
        Args:
            ref_measurement (Measurement): The reference measurement.
            eval_measurement (Measurement): The evaluation measurement.
        Requirements:
            - the sample rates of the measurements match.
        Attributes:
            ref_sync_start (int): The start index of the reference synchronization block.
            eval_sync_start (int): The start index of the evaluation synchronization block.
            ref_sync_end (int): The end index of the reference synchronization block.
            eval_sync_end (int): The end index of the evaluation synchronization block.
            sync_blocks (list[SyncBlock]): A list of synchronization blocks.
            sample_rate (int): The sample rate of the measurements.
            metric: The metric used for comparison.
        Example:
            ref_measurement = Measurement(...)
            eval_measurement = Measurement(...)
            comparison = Comparison(ref_measurement, eval_measurement)
        """
        self.ref_measurement = ref_measurement
        self.eval_measurement = eval_measurement
        self.logger = logging.getLogger(__name__)
        self.channel_assignments = {}
        mes2_channel_names = [
            channel.name for channel in eval_measurement.channels]
        for channel in ref_measurement.channels:
            if channel.name in mes2_channel_names:
                self.channel_assignments[channel.name] = channel.name
                continue
            self.channel_assignments[channel.name] = None

        if ref_measurement.sample_rate != eval_measurement.sample_rate:
            self.logger.error("Sample rates of measurements do not match")
            return

        self.sync_blocks: list[SyncBlock] = []
        self.sample_rate = ref_measurement.sample_rate
        self.metric = None

    def assign_channel(self, channel1: str, channel2: str):
        self.channel_assignments[channel1] = channel2

    def get_assigned_channel(self, channel1: str) -> str:
        return self.channel_assignments[channel1]

    def get_channels(self) -> list[tuple[Channel, Channel]]:
        return [(self.ref_measurement.get_channel_by_name(channel1), self.eval_measurement.get_channel_by_name(channel2))
                for channel1, channel2 in self.channel_assignments.items() if channel2 is not None]

    def set_metric(self, metric: Metric):
        self.metric = metric

    def add_sync_block(self, sync_block: SyncBlock):
        """
        Adds a sync block to the list of sync blocks.
        Requirements:
            - The sync block must not overlap with the previous sync block in the list.
        Parameters:
            sync_block (SyncBlock): The sync block to be added.
        """
        if len(self.sync_blocks) == 0:
            self.sync_blocks.append(sync_block)
            return

        last_sync_block = self.sync_blocks[-1]
        if sync_block.ref_start < last_sync_block.ref_end:
            self.logger.error("Sync block overlaps with previous sync block")
            return
        self.sync_blocks.append(sync_block)

    def copy(self) -> 'Comparison':
        """
        Creates a copy of the comparison.
        Returns:
            Comparison: The copy of the comparison.
        """
        comparison = Comparison(self.ref_measurement, self.eval_measurement)
        comparison.sync_blocks = [sync_block
                                  for sync_block in self.sync_blocks]
        comparison.metric = self.metric
        comparison.channel_assignments = self.channel_assignments.copy()
        return comparison
