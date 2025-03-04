from logging import getLogger
from .signal_data import SignalData
from .metric_result import MetricResult
from .metric import Metric
import numpy as np


class PearsonCorrelationMetric(Metric):

    def __init__(self):
        self.logger = getLogger(__name__)

    def __call__(self, ref_channel: SignalData, eval_channel: SignalData) -> MetricResult:
        ref_values = ref_channel.values
        eval_values = eval_channel.values
        length = len(ref_values)

        correlation = self.pearson_correlation(ref_values, eval_values)
        result = np.full(length, correlation)

        return MetricResult(ref_channel, eval_channel, SignalData(ref_channel.timestamps, result), {}, {})

    def pearson_correlation(self, a: np.ndarray, b: np.ndarray) -> float:
        mean_a = a.mean()
        mean_b = b.mean()
        upper = np.sum((a - mean_a) * (b - mean_b))
        lower = np.sqrt(np.sum((a - mean_a) ** 2)
                        * np.sum((b - mean_b) ** 2))
        if lower == 0:
            return 0

        correlation = upper / lower

        scaled_correlation = (correlation + 1) / 2

        return scaled_correlation

    def __str__(self):
        return f"Pearson Correlation"
