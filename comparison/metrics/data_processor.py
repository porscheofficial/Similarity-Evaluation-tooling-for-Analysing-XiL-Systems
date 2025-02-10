

import numpy as np
from comparison.metrics.metric_result import MetricResult
from comparison.sync_block import SyncBlock
from .signal_data import SignalData


class DataProcessor:

    def shift_signal(self, signal_data: SignalData, shift: float):
        """
        Shifts the signal data by the given shift value.

        Parameters
        ----------
        signal_data : SignalData
            Signal data to shift.
        shift : float
            Shift value.
        """
        return SignalData(signal_data.timestamps + shift, signal_data.values)

    def shift_metric_result(self, metric_result: MetricResult, shift: float):
        """
        Shifts the metric result by the given shift value.

        Parameters
        ----------
        metric_result : MetricResult
            Metric result to shift.
        shift : float
            Shift value.
        """

        ref_in = self.shift_signal(metric_result.reference_input, shift)
        eval_in = self.shift_signal(metric_result.evaluated_input, shift)
        result = self.shift_signal(metric_result.result, shift)
        result_metadata = {}
        for key, metadata in metric_result.result_metadata.items():
            result_metadata[key] = self.shift_signal(metadata, shift)
        input_metadata = {}
        for key, metadata in metric_result.input_metadata.items():
            input_metadata[key] = self.shift_signal(metadata, shift)

        return MetricResult(ref_in, eval_in, result, result_metadata, input_metadata)

    def concat_signal_data(self, prev: SignalData, next: SignalData):
        """
        Concatenates the next signal data to the previous signal data.

        Parameters
        ----------
        prev : SignalData
            Previous signal data.
        next : SignalData
            Next signal data.
        """
        prev_sample_rate = 0
        next_t_shift = 0
        if len(prev.timestamps) > 1:
            prev_sample_rate = prev.timestamps[1] - prev.timestamps[0]
            next_t_shift = prev.timestamps[-1] + prev_sample_rate

        next_timestamps = next.timestamps + next_t_shift

        timestamps = np.concatenate([prev.timestamps, next_timestamps])
        values = np.concatenate([prev.values, next.values])

        return SignalData(timestamps, values)

    def concat_metric_result(self, prev: MetricResult, next: MetricResult):
        """
        Concatenates the next metric result to the previous metric result.

        Parameters
        ----------
        prev : MetricResult
            Previous metric result.
        next : MetricResult
            Next metric result.
        """
        ref_in = self.concat_signal_data(
            prev.reference_input, next.reference_input)
        eval_in = self.concat_signal_data(
            prev.evaluated_input, next.evaluated_input)
        result = self.concat_signal_data(prev.result, next.result)
        result_metadata = {}
        for key, metadata in prev.result_metadata.items():
            result_metadata[key] = self.concat_signal_data(
                metadata, next.result_metadata[key])
        input_metadata = {}
        for key, metadata in prev.input_metadata.items():
            input_metadata[key] = self.concat_signal_data(
                metadata, next.input_metadata[key])

        return MetricResult(ref_in, eval_in, result, result_metadata, input_metadata)

    def apply_sync_block(self, ref_data: SignalData, eval_data: SignalData, sync_block: SyncBlock):
        """
        Applies a synchronization block to the reference and evaluation data.

        Args:
            ref_data (SignalData): The reference data to be synchronized.
            eval_data (SignalData): The evaluation data to be synchronized.
            sync_block (SyncBlock): The synchronization block to be applied.

        Returns:
            tuple[SignalData, SignalData]: A tuple containing the synchronized reference and evaluation data.
        """
        time_step = ref_data.sample_time_step
        ref_start_step = int(sync_block.ref_start / time_step)
        eval_start_step = int(sync_block.eval_start / time_step)
        length = int((sync_block.ref_end - sync_block.ref_start) / time_step)
        other_length = int(
            (sync_block.eval_end - sync_block.eval_start) / time_step)
        if length != other_length:
            raise ValueError("Lengths of the sync blocks do not match")
        ref_start_time = ref_start_step * time_step
        eval_start_time = eval_start_step * time_step

        ref_timestamps = ref_data.timestamps - ref_start_time
        eval_timestamps = eval_data.timestamps - eval_start_time
        ref_timestamps = ref_timestamps[ref_start_step:ref_start_step + length]
        eval_timestamps = eval_timestamps[eval_start_step:eval_start_step + length]
        ref_values = ref_data.values[ref_start_step:ref_start_step + length]
        eval_values = eval_data.values[eval_start_step:eval_start_step + length]

        return SignalData(ref_timestamps, ref_values), SignalData(eval_timestamps, eval_values)
