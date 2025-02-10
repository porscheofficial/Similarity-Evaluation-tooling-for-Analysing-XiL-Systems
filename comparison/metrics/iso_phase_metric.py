from logging import getLogger

from .signal_data import SignalData

from .metric_result import MetricResult
from .metric import Metric
import numpy as np


class IsoPhaseMetric(Metric):
    """
    IsoPhaseMetric is a class that calculates the phase alignment score between two input channels and provides the phase-aligned signals.

    This metric is used to align two signals (channel_a and channel_b) in phase by calculating the cross-correlation and determining the optimal shift. The class then computes a phase score based on the alignment.

    Attributes:
        logger (Logger): Logger instance for logging information.
        allowable_time_shift (float): Maximum allowable time shift as a fraction of the signal length.
        regression_factor (int): Factor used for regression calculations.

    Methods:
        __call__(channel_a: SignalData, channel_b: SignalData) -> MetricResult:
            Aligns the input channels in phase, calculates the phase score, and returns the metric result.

        cross_correlation_left_shift(a: np.ndarray, b: np.ndarray, shift: int) -> float:
            Calculates the cross-correlation for a left shift.

        cross_correlation_right_shift(a: np.ndarray, b: np.ndarray, shift: int) -> float:
            Calculates the cross-correlation for a right shift.

        cross_correlation(a: np.ndarray, b: np.ndarray) -> float:
            Calculates the cross-correlation between two signals.

        phase_score(a: np.ndarray, b: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
            Calculates the phase score between two signals and returns the shifted signals with the highest correlation.

    Metadata:
        The metadata included in the MetricResult contains:
            - shifted_a (SignalData): The phase-aligned version of channel_a.
            - shifted_b (SignalData): The phase-aligned version of channel_b.
    """

    def __init__(self, allowed_time_shift: float = 0.2) -> None:
        super().__init__()
        self.logger = getLogger("Metric")
        self.allowable_time_shift = allowed_time_shift
        self.regression_factor = 1

    def __call__(self, reference_channel: SignalData, evaluated_channel: SignalData) -> MetricResult:

        phase_score, ref_shifted, eval_shifted = self.phase_score(
            reference_channel, evaluated_channel)

        phase_score_array = np.full(
            reference_channel.values.shape, phase_score)
        timestamps = reference_channel.timestamps

        result_data = SignalData(timestamps, phase_score_array)

        return MetricResult(reference_channel, evaluated_channel, result_data, {}, {
            "shifted_a": ref_shifted,
            "shifted_b": eval_shifted
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
        return upper / lower

    def phase_score(self, reference: SignalData, evaluated: SignalData) -> tuple[float, SignalData, SignalData]:
        """
        Calculate the phase score between two signals, as well as the shifted signals with the highest correlation
        :param a: Signal A
        :param b: Signal B
        :return: Tuple with the phase score and the shifted signals
        """
        reference_values = reference.values
        evaluated_values = evaluated.values
        max_allowed_shift = int(
            self.allowable_time_shift * len(reference_values))
        left_shifts = np.array([self.cross_correlation_left_shift(
            reference_values, evaluated_values, i) for i in range(max_allowed_shift + 2)])
        right_shifts = np.array([self.cross_correlation_right_shift(reference_values, evaluated_values, i)
                                 for i in range(max_allowed_shift + 2)])
        best_left = np.argmax(left_shifts)
        best_right = np.argmax(right_shifts)
        best = best_left
        shifted_reference_values = reference_values[best:]
        shifted_evaluated_values = evaluated_values[:len(evaluated) - best]
        shifted_reference_timestamps = reference.timestamps[best:]
        shifted_evaluated_timestamps = evaluated.timestamps[best:]
        if right_shifts[best_right] > left_shifts[best_left]:
            best = best_right
            shifted_reference_values = reference_values[:len(reference) - best]
            shifted_evaluated_values = evaluated_values[best:]
            shifted_reference_timestamps = reference.timestamps[best:]
            shifted_evaluated_timestamps = evaluated.timestamps[best:]

        shifted_reference = SignalData(
            shifted_reference_timestamps, shifted_reference_values)
        shifted_evaluated = SignalData(
            shifted_evaluated_timestamps, shifted_evaluated_values)

        if best == 0:
            return 1, reference, evaluated

        return max(0, ((max_allowed_shift - best) / max_allowed_shift) ** self.regression_factor), shifted_reference, shifted_evaluated

    def __str__(self):
        return f"IsoPhaseMetric ({self.allowable_time_shift})"
