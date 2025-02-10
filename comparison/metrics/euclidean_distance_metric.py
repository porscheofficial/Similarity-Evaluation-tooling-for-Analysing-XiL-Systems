
from logging import getLogger
import numpy as np

from .metric_result import MetricResult
from .signal_data import SignalData
from .metric import Metric


class EuclideanDistanceMetric(Metric):
    def __init__(self):
        super().__init__()
        self.logger = getLogger(__name__)

    def __call__(self, ref_channel: SignalData, eval_channel: SignalData) -> MetricResult:

        amplitude = max(ref_channel.amplitude(), eval_channel.amplitude(), 0.00001)
        length = ref_channel.shape[0]

        differences = (ref_channel.values -
                       eval_channel.values) ** 2

        total_difference = np.sum(differences)
        euclidean_distance = np.sqrt(total_difference)
        max_result = np.sqrt((amplitude ** 2) * length)
        euclidean_distance_norm = 1 - (euclidean_distance / max_result)

        self.logger.info(
            f"The euclidean distance was calculated as {euclidean_distance} with the maximal possible distance being {max_result} therefore it was normalized to {euclidean_distance_norm}")

        parts = 1 - (differences / (amplitude ** 2))
        parts_sum = np.sum(parts)
        if parts_sum == 0:
            parts = np.ones(length)
        else:
            parts = (parts * length) / parts_sum

        parts = parts * euclidean_distance_norm

        return MetricResult(ref_channel, eval_channel, SignalData(ref_channel.timestamps, parts), {}, {})

    def __str__(self) -> str:
        return f"Euclidean Distance"
