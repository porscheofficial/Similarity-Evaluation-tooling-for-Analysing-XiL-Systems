from .signal_data import SignalData
from .metric import Metric
from .metric_result import MetricResult
from .iso_phase_metric import IsoPhaseMetric
import numpy as np
from logging import getLogger


class IsoSlopeMetric(Metric):
    """
    IsoSlopeMetric is a class that calculates the average slope of two input channels after phase alignment.

    This metric is used to compare the slopes of two signals (channel_a and channel_b) by first aligning them in phase using the IsoPhaseMetric. The class then computes the average slope of the phase-aligned signals and compares them.

    Attributes:
        logger (Logger): Logger instance for logging information.
        regression_factor (int): Factor used for regression calculations.
        max_error (float): Maximum allowable error for the metric.

    Methods:
        __call__(channel_a: np.ndarray, channel_b: np.ndarray) -> MetricResult:
            Aligns the input channels in phase, calculates their average slopes, and returns the metric result.

        calculate_average_slope(signal: np.ndarray) -> np.ndarray:
            Calculates the average slope of the given signal.

        slope_score(a_slope: SignalData, b_slope: SignalData) -> float:
            Calculates the slope score based on the average slopes of the two channels.

    Metadata:
        The metadata included in the MetricResult contains:
            - a_slope (SignalData): The average slope of the phase-aligned channel_a.
            - b_slope (SignalData): The average slope of the phase-aligned channel_b.
    """

    def __init__(self) -> None:
        super().__init__()
        self.logger = getLogger("Metric")
        self.regression_factor = 1
        self.max_error = 2.0

    def __call__(self, ref_channel: SignalData, eval_channel: SignalData) -> MetricResult:

        phase_result = IsoPhaseMetric()(ref_channel, eval_channel)
        shifted_ref = phase_result.input_metadata["shifted_a"]
        shifted_eval = phase_result.input_metadata["shifted_b"]

        ref_slope = self.calculate_average_slope(shifted_ref.values)
        eval_slope = self.calculate_average_slope(shifted_eval.values)

        slope_score = self.slope_score(ref_slope, eval_slope)

        slope_score_array = np.full(ref_channel.values.shape, slope_score)

        return MetricResult(ref_channel, eval_channel, SignalData(ref_channel.timestamps, slope_score_array), {}, {
            "a_slope": SignalData(shifted_ref.timestamps, ref_slope),
            "b_slope": SignalData(shifted_eval.timestamps, eval_slope)
        })

    def calculate_average_slope(self, signal: np.ndarray) -> float:
        length = len(signal)

        slope = np.zeros_like(signal)
        for i in range(length):
            if i == 0:
                slope[i] = (signal[i + 1] - signal[i]) / 1
            elif i == length - 1:
                slope[i] = (signal[i] - signal[i - 1]) / 1
            else:
                slope[i] = (signal[i + 1] - signal[i - 1]) / 2

        average_slope = np.zeros_like(signal)
        for i in range(length):
            if i < 4:
                average_slope[i] = np.mean(slope[:i + i + 1])
            elif i >= length - 4:
                to_end = length - i - 1
                average_slope[i] = np.mean(slope[i - to_end:])
            else:
                average_slope[i] = np.mean(slope[i - 4:i + 5])

        return average_slope

    def slope_score(self, a_slope: np.ndarray, b_slope: np.ndarray) -> float:
        b_slope_norm = np.linalg.norm(b_slope)

        if b_slope_norm == 0:
            self.logger.warning(
                "Norm of channel B slope is 0, setting slope score to 1")
            return 1

        epsilon_slope = np.linalg.norm(
            a_slope - b_slope) / b_slope_norm
        return max(0, (self.max_error - epsilon_slope) / self.max_error) ** self.regression_factor
    
    def __str__(self):
        return "IsoSlopeMetric"
