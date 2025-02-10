from logging import getLogger

from .signal_data import SignalData

from .metric_result import MetricResult
from .metric import Metric
import numpy as np


class IsoCorridorMetric(Metric):
    """
    IsoCorridorMetric is a class that calculates a corridor-based similarity score between two input channels.

    This metric is used to compare two signals (channel_a and channel_b) by defining inner and outer corridors around channel_a. The similarity score is calculated based on how well channel_b fits within these corridors.

    Attributes:
        logger (Logger): Logger instance for logging information.
        inner_corridor_a0 (float): Scaling factor for the inner corridor.
        outer_corridor_b0 (float): Scaling factor for the outer corridor.
        regression_factor (int): Factor used for regression calculations.

    Methods:
        __call__(channel_a: SignalData, channel_b: SignalData) -> MetricResult:
            Calculates the corridor-based similarity score and returns the metric result.

        _corridor_func(inner: float, outer: float, a: float, b: float) -> float:
            Determines the similarity score for a pair of values based on the defined corridors.

    Metadata:
        The metadata included in the MetricResult contains:
            - outer_corridor_top (np.ndarray): The upper boundary of the outer corridor.
            - inner_corridor_top (np.ndarray): The upper boundary of the inner corridor.
            - outer_corridor_bottom (np.ndarray): The lower boundary of the outer corridor.
            - inner_corridor_bottom (np.ndarray): The lower boundary of the inner corridor.
    """

    def __init__(self) -> None:
        super().__init__()
        self.logger = getLogger("Metric")
        self.inner_corridor_a0 = 0.05
        self.outer_corridor_b0 = 0.5
        self.regression_factor = 2

    def __call__(self, ref_channel: SignalData, eval_channel: SignalData) -> MetricResult:

        amplitude = ref_channel.amplitude()
        inner_corridor = amplitude * self.inner_corridor_a0
        outer_corridor = amplitude * self.outer_corridor_b0

        if amplitude == 0:
            self.logger.warning(f"Amplitude of reference channel is 0!")

        corridor = np.array([self._corridor_func(inner_corridor, outer_corridor, a, b)
                             for a, b in zip(ref_channel.values, eval_channel.values)])

        outer_corridor_top = np.full(
            ref_channel.shape, outer_corridor) + ref_channel.values
        inner_corridor_top = np.full(
            ref_channel.shape, inner_corridor) + ref_channel.values
        outer_corridor_bottom = ref_channel.values - \
            np.full(ref_channel.shape, outer_corridor)
        inner_corridor_bottom = ref_channel.values - \
            np.full(ref_channel.shape, inner_corridor)

        return MetricResult(ref_channel, eval_channel, SignalData(ref_channel.timestamps, corridor), {}, {
            "outer_corridor_top": SignalData(ref_channel.timestamps, outer_corridor_top),
            "inner_corridor_top": SignalData(ref_channel.timestamps, inner_corridor_top),
            "outer_corridor_bottom": SignalData(ref_channel.timestamps, outer_corridor_bottom),
            "inner_corridor_bottom": SignalData(ref_channel.timestamps, inner_corridor_bottom)
        })

    def _corridor_func(self, inner: float, outer: float, a: float, b: float) -> float:

        if inner == 0:
            return 1 if a == b else 0

        diff = abs(a - b)
        if diff < inner:
            return 1
        if diff > outer:
            return 0
        return ((outer - diff) / (outer - inner)) ** self.regression_factor

    def __str__(self) -> str:
        return f"IsoCorridorMetric ({self.inner_corridor_a0}, {self.outer_corridor_b0}, {self.regression_factor})"
