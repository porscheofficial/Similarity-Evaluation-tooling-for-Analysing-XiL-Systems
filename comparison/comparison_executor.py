
from logging import getLogger

from PySide6.QtCore import QObject, Signal, QThread
from more_itertools import chunked, flatten

from .metrics import DataProcessor
from comparison.metrics.metric_result import MetricResult
from comparison.metrics.signal_data import SignalData
from comparison.sync_block import SyncBlock
from comparison.sync_processor import SyncProcessor
from measurement.channel.channel import Channel
from measurement.channel.channel_data import ChannelData
from measurement.channel.channel_data_repository import ChannelDataRepository
from measurement.channel.channel_processor import ChannelProcessor

from .comparison import Comparison
from .comparison_result import ComparisonResult
from .metrics.metric import Metric

import numpy as np

import multiprocessing as mp


class ComparisonExecutor(QThread):
    """A QThread subclass that executes measurement comparisons asynchronously.
    This class handles the execution of measurement comparisons in a separate thread
    to prevent blocking the main GUI thread. It emits a signal when the
    comparison is complete.
    Attributes:
        done (Signal): Signal emitted when comparison is complete, carries ComparisonResult
        comparison (Comparison): The comparison configuration to execute
        logger (Logger): Logger instance for this class
        comparison_result (ComparisonResult): Stores the result of the comparison
    Signals:
        done (ComparisonResult): Emitted when comparison is complete
    Args:
        comparison (Comparison): The comparison configuration to execute
    """
    done = Signal(ComparisonResult)

    def __init__(self, comparison: Comparison):
        super().__init__()
        self.comparison = comparison
        self.logger = getLogger(__name__)
        self.comparison_result = None

        if len(self.comparison.sync_blocks) == 0:
            self.logger.error("No sync blocks to compare!!")

    def run(self) -> None:
        self.comparison_result = execute_comparison(self.comparison, None)
        if self.comparison_result is not None:
            self.done.emit(self.comparison_result)


class MultiComparisonExecutor(QThread):
    """
    A QThread subclass that executes multiple comparisons in parallel using a multiprocessing pool.
    This class handles the execution of a list of comparisons, emitting signals for both
    individual comparison completion and overall completion of all comparisons.
    Signals:
        donePart (ComparisonResult): Emitted when a single comparison is completed.
        doneAll (list): Emitted when all comparisons are completed, containing all results.
    Args:
        comparisons (list[Comparison]): A list of Comparison objects to be executed.
    Attributes:
        comparisons (list[Comparison]): The list of comparisons to be executed.
        logger (Logger): Logger instance for this class.
        comparison_results (list): List to store the results of completed comparisons.
    """
    donePart = Signal(ComparisonResult)
    doneAll = Signal(list)

    def __init__(self, comparisons: list[Comparison]):
        super().__init__()
        self.comparisons = comparisons
        self.logger = getLogger(__name__)
        self.comparison_results = []

    def run(self) -> None:
        pool = mp.Pool(mp.cpu_count() // 2)
        self.logger.info(f"Starting {len(self.comparisons)} comparisons")
        for comparison in self.comparisons:
            comparison_result = execute_comparison(comparison, pool)
            if comparison_result is not None:
                self.logger.info(f"Comparison done: {comparison_result.name}")
                self.comparison_results.append(comparison_result)
                self.donePart.emit(comparison_result)
            else:
                self.logger.warning(
                    f"Comparison failed: {comparison.ref_measurement.name} - {comparison.eval_measurement.name} ({str(comparison.metric)})")
        self.logger.info("All comparisons done")
        self.doneAll.emit(self.comparison_results)


def execute_comparison(comparison: Comparison, pool) -> ComparisonResult:
    """Executes a comparison between two measurements using a specified metric.
    This function is used in the comparison tool to perform channel-by-channel comparisons 
    between reference and evaluation measurements. It supports both single-threaded and 
    multi-threaded execution using a process pool.
    Args:
        comparison (Comparison): Object containing reference measurement, evaluation measurement, 
                               metric and synchronization blocks information.
        pool: Multiprocessing pool for parallel execution. If None, runs in single thread.
    Returns:
        ComparisonResult: Object containing all individual channel comparison results and total metrics.
                         Returns None if no channels to compare or sample rates don't match.
    Notes:
        - Both measurements must have matching sample rates
        - Channels are processed in chunks for better performance
        - Used in comparison_tool.py when executing measurement comparisons
        - Handles automatic chunking of channel pairs for parallel processing
    Example usage:
        result = execute_comparison(comparison_obj, multiprocessing.Pool())
    """
    logger = getLogger(__name__)
    comparison_result = ComparisonResult(
        f"{comparison.ref_measurement.name} - {comparison.eval_measurement.name} ({str(comparison.metric)})")
    channel_pairs = comparison.get_channels()
    metric: Metric = comparison.metric
    ref_measurement = comparison.ref_measurement
    eval_measurement = comparison.eval_measurement

    logger.info("Starting comparison")

    if len(channel_pairs) == 0:
        logger.error("No channels to compare")
        return None

    if ref_measurement.sample_rate != eval_measurement.sample_rate:
        logger.error("Sample rates of measurements do not match")
        return None

    chunk_size = 250 if len(
        channel_pairs) > 500 else max(1, len(channel_pairs) // 4)

    chunks = list(chunked(channel_pairs, chunk_size))
    logger.info(f"Comparing {len(channel_pairs)} channels in {len(chunks)} chunks")

    if pool is None:
        logger.info("Running comparison in single thread")
        results = [compare_chunk(
            chunk, metric, comparison.sync_blocks) for chunk in chunks]
    else:
        results = pool.starmap(compare_chunk, [(
            chunk, metric, comparison.sync_blocks) for chunk in chunks])

    for ref_ch, eval_ch, result in flatten(results):
        comparison_result.add_result(ref_ch, eval_ch, result)

    logger.info("Comparison done")
    comparison_result.calculate_total()
    return comparison_result


def compare_chunk(chunk: list[tuple[Channel, Channel]], metric: Metric, sync_blocks: list[SyncBlock]) -> list[tuple[ChannelData, ChannelData, MetricResult]]:
    logger = getLogger("Compare Chunk")
    logger.info(f"Comparing chunk with {len(chunk)} pairs")
    results = []
    repository = ChannelDataRepository()
    processor = DataProcessor()
    for ref_channel, eval_channel in chunk:
        ref_chdata = repository.load_from_channel(ref_channel)
        eval_chdata = repository.load_from_channel(eval_channel)
        if len(ref_chdata.timestamps()) < 10 or len(eval_chdata.timestamps()) < 10:
            logger.warning(
                f"Channel {ref_chdata.name} is very short ({len(ref_chdata.timestamps())} samples, {len(eval_chdata.timestamps())} samples)")

        final_result = None
        sync_ref_data = SignalData.empty()
        sync_eval_data = SignalData.empty()
        ref_data = SignalData.from_channel_data(ref_chdata)
        eval_data = SignalData.from_channel_data(eval_chdata)
        for sync_block in sync_blocks:
            block_ref_data, block_eval_data = processor.apply_sync_block(
                ref_data, eval_data, sync_block)
            sync_ref_data = processor.concat_signal_data(
                sync_ref_data, block_ref_data)
            sync_eval_data = processor.concat_signal_data(
                sync_eval_data, block_eval_data)

        final_result = metric(sync_ref_data, sync_eval_data)
        results.append((ref_chdata, eval_chdata, final_result))
    return results


def compare_individual(ref_channel: ChannelData, eval_channel: ChannelData, metric: Metric, sync_block: SyncBlock):
    logger = getLogger("Compare Chunk")
    data_processor = DataProcessor()
    ref_data = SignalData.from_channel_data(ref_channel)
    eval_data = SignalData.from_channel_data(eval_channel)

    ref_synced, eval_synced = data_processor.apply_sync_block(
        ref_data, eval_data, sync_block)

    if len(ref_synced.timestamps) < 10 or len(eval_synced.timestamps) < 10:
        logger.warning(
            f"Sync times are {sync_block.ref_start} - {sync_block.ref_end}, {sync_block.eval_start} - {sync_block.eval_end}")
        logger.warning(
            f"Channel {ref_channel.name} is very short after synchronization ({len(ref_data.timestamps)} samples, {len(eval_data.timestamps)} samples)")

    result = metric(ref_synced, eval_synced)
    result = data_processor.shift_metric_result(result, sync_block.ref_start)

    return result
