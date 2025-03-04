import numpy as np
from .metric_result import MetricResult
from .signal_data import SignalData
from .metric import Metric


class CorridorMetric(Metric):

    def __init__(self, inner: float, outer: float, delay_inner: float, delay_outer: float) -> None:
        self.inner = inner
        self.outer = outer
        self.delay_inner = delay_inner
        self.delay_outer = delay_outer
        self.regression = 2

    def __call__(self, ref_channel: SignalData, eval_channel: SignalData) -> MetricResult:
        amplitude = ref_channel.amplitude()
        if amplitude == 0:
            amplitude = 1

        result = np.zeros_like(ref_channel.values)

        for i in range(len(ref_channel.values)):
            value = eval_channel.values[i]

            vertical_dist = np.abs(ref_channel.values - value)
            vertical_dist = vertical_dist - (amplitude * self.inner)
            vertical_dist = vertical_dist / \
                (amplitude * (self.outer - self.inner))
            vertical_dist = np.clip(vertical_dist, 0, 1)

            horizontal_dist = np.abs(
                ref_channel.timestamps - eval_channel.timestamps[i])
            horizontal_dist = horizontal_dist - self.delay_inner
            horizontal_dist = horizontal_dist / \
                (self.delay_outer - self.delay_inner)
            horizontal_dist = np.clip(horizontal_dist, 0, 1)

            dist = np.sqrt(
                vertical_dist ** self.regression + horizontal_dist ** self.regression)

            result[i] = 1 - np.min(dist)

        result = SignalData(ref_channel.timestamps, result)

        return MetricResult(ref_channel, eval_channel, result, {}, {})

    def __str__(self) -> str:
        return f"Corridor ({self.inner}, {self.outer}, {self.delay_inner}, {self.delay_outer})"
