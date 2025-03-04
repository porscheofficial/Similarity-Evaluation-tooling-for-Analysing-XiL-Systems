from .signal_data import SignalData
from .metric_result import MetricResult
from .metric import Metric
import numpy as np


class CrossCorrelationMetric(Metric):

    def __init__(self, allowed_time_shift: float):
        self.allowed_time_shift = allowed_time_shift

    def __call__(self, ref_channel: SignalData, eval_channel: SignalData) -> MetricResult:
        ref_values = ref_channel.values
        eval_values = eval_channel.values
        length = len(ref_values)
        max_allowed_shift = int(
            self.allowed_time_shift * len(ref_values))
        left_shifts = np.array([self.cross_correlation_left_shift(
            ref_values, eval_values, i) for i in range(max_allowed_shift + 2)])
        right_shifts = np.array([self.cross_correlation_right_shift(ref_values, eval_values, i)
                                 for i in range(max_allowed_shift + 2)])
        best_left = np.argmax(left_shifts)
        best_right = np.argmax(right_shifts)
        best = best_left
        result = np.full(length, left_shifts[best])
        shifted_reference_values = ref_values[best:]
        shifted_evaluated_values = eval_values[:length - best]
        shifted_reference_timestamps = ref_channel.timestamps[best:]
        shifted_evaluated_timestamps = eval_channel.timestamps[best:]
        if right_shifts[best_right] > left_shifts[best_left]:
            best = best_right
            result = np.full(length, right_shifts[best])
            shifted_reference_values = ref_values[:length - best]
            shifted_evaluated_values = eval_values[best:]
            shifted_reference_timestamps = ref_channel.timestamps[best:]
            shifted_evaluated_timestamps = eval_channel.timestamps[best:]

        ref_shifted = SignalData(
            shifted_reference_timestamps, shifted_reference_values)
        eval_shifted = SignalData(
            shifted_evaluated_timestamps, shifted_evaluated_values)

        return MetricResult(ref_channel, eval_channel, SignalData(ref_channel.timestamps, result), {}, {
            "ref_shifted": ref_shifted,
            "eval_shifted": eval_shifted
        })

    def cross_correlation_left_shift(self, a: np.ndarray, b: np.ndarray, shift: int) -> float:
        shifted_a = a[shift:]
        shifted_b = b[:len(b) - shift]
        return self.cross_correlation(shifted_a, shifted_b)

    def cross_correlation_right_shift(self, a: np.ndarray, b: np.ndarray, shift: int) -> float:
        shifted_a = a[:len(a) - shift]
        shifted_b = b[shift:]
        return self.cross_correlation(shifted_a, shifted_b)

    def cross_correlation(self, a: np.ndarray, b: np.ndarray) -> float:
        mean_a = a.mean()
        mean_b = b.mean()
        upper = np.sum((a - mean_a) * (b - mean_b))
        lower = np.sqrt(np.sum((a - mean_a) ** 2)
                        * np.sum((b - mean_b) ** 2))
        if lower == 0:
            return 0

        cross_correlation = upper / lower

        scaled_cross_correlation = (cross_correlation + 1) / 2

        return scaled_cross_correlation

    def __str__(self):
        return f"CrossCorrelationMetric ({self.allowed_time_shift})"
