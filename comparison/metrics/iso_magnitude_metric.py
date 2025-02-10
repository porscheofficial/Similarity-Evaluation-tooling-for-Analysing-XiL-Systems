from logging import getLogger

from .signal_data import SignalData
from .metric import Metric
from .metric_result import MetricResult
from .iso_phase_metric import IsoPhaseMetric

import matplotlib.pyplot as plt

import numpy as np


class IsoMagnitudeMetric(Metric):
    """
    IsoMagnitudeMetric is a class that calculates the magnitude alignment score between two input channels after phase alignment and dynamic time warping.

    This metric is used to compare the magnitudes of two signals (reference and evaluated) by first aligning them in phase using the IsoPhaseMetric, then performing dynamic time warping (DTW) to align them in time. The class then computes a magnitude score based on the alignment.

    Attributes:
        logger (Logger): Logger instance for logging information.
        allowable_time_shift (float): Maximum allowable time shift as a fraction of the signal length.
        regression_factor (int): Factor used for regression calculations.
        max_error (float): Maximum allowable error for the metric.

    Methods:
        __call__(reference_channel: np.ndarray, evaluated_channel: np.ndarray) -> MetricResult:
            Aligns the input channels in phase, performs dynamic time warping, calculates the magnitude score, and returns the metric result.

        dynamic_time_warping(ref_shifted: np.ndarray, eval_shifted: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            Performs dynamic time warping (DTW) on two phase-aligned signals and returns the warped signals.

        magnitude_score(ref_warped: np.ndarray, eval_warped: np.ndarray) -> float:
            Calculates the magnitude score based on the warped signals.

    Metadata:
        The metadata included in the MetricResult contains:
            - ref_warped (np.ndarray): The time-warped version of reference_channel.
            - eval_warped (np.ndarray): The time-warped version of evaluated_channel.
    """

    def __init__(self) -> None:
        super().__init__()
        self.logger = getLogger("Metric")
        self.time_warping_window = 0.1
        self.regression_factor = 1
        self.max_error = 0.5

    def __call__(self, reference_channel: SignalData, evaluated_channel: SignalData) -> MetricResult:

        phase_result = IsoPhaseMetric()(reference_channel, evaluated_channel)
        shifted_a = phase_result.input_metadata["shifted_a"]
        shifted_b = phase_result.input_metadata["shifted_b"]

        ref_warped, eval_warped = self.dynamic_time_warping(
            shifted_a, shifted_b)

        magnitude_score = self.magnitude_score(
            ref_warped.values, eval_warped.values)

        magnitude_score_array = np.full(
            reference_channel.values.shape, magnitude_score)

        return MetricResult(reference_channel, evaluated_channel, SignalData(reference_channel.timestamps, magnitude_score_array), {}, {
            "ref_warped": ref_warped,
            "eval_warped": eval_warped
        })

    def dynamic_time_warping(self, ref_shifted: SignalData, eval_shifted: SignalData) -> tuple[SignalData, SignalData]:
        """
        Perform dynamic time warping (DTW) on two signals
        """
        signal_length = len(ref_shifted)
        window = int(signal_length * self.time_warping_window)

        dtw_matrix = np.full((signal_length, signal_length), np.inf)
        pure_dtw_matrix = np.full((signal_length, signal_length), np.inf)

        ref_shifted_values = ref_shifted.values
        eval_shifted_values = eval_shifted.values

        for i in range(signal_length):
            for j in range(max(0, i - window), min(signal_length, i + window)):
                d_cost = (ref_shifted_values[i] - eval_shifted_values[j]) ** 2
                pure_dtw_matrix[i, j] = d_cost
                if i == 0 and j == 0:
                    dtw_matrix[i, j] = d_cost
                    continue
                if i == 0:
                    dtw_matrix[i, j] = d_cost + dtw_matrix[i, j - 1]
                    continue
                if j == 0:
                    dtw_matrix[i, j] = d_cost + dtw_matrix[i - 1, j]
                    continue
                dtw_matrix[i, j] = d_cost + min(dtw_matrix[i - 1, j],
                                                dtw_matrix[i, j - 1], dtw_matrix[i - 1, j - 1])

        self.logger.info("DTW matrix calculated")

        i, j = signal_length - 1, signal_length - 1
        path = []
        while i > 0 and j > 0:
            path.append((i, j))

            if i == 0:
                j -= 1
                continue
            if j == 0:
                i -= 1
                continue
            i, j = min((i - 1, j), (i, j - 1), (i - 1, j - 1),
                       key=lambda x: dtw_matrix[x[0], x[1]])

        path.append((0, 0))
        path.reverse()

        ref_warped_values = np.array([ref_shifted_values[i] for i, _ in path])
        eval_warped_values = np.array(
            [eval_shifted_values[j] for _, j in path])
        warped_timestamps = np.array(
            [(ref_shifted.timestamps[i] + eval_shifted.timestamps[j]) / 2 for i, j in path])

        ref_warped = SignalData(warped_timestamps, ref_warped_values)
        eval_warped = SignalData(warped_timestamps, eval_warped_values)

        return ref_warped, eval_warped

    def magnitude_score(self, ref_warped: np.ndarray, eval_warped: np.ndarray) -> float:
        ref_norm = np.linalg.norm(ref_warped)
        if ref_norm == 0:
            self.logger.warning(
                "Norm of reference channel warped is 0, setting magnitude score to 1")
            return 1
        epsilon_mag = np.linalg.norm(
            eval_warped - ref_warped) / ref_norm

        return max(0, (self.max_error - epsilon_mag) / self.max_error) ** self.regression_factor

    def __str__(self) -> str:
        return "IsoMagnitudeMetric"
