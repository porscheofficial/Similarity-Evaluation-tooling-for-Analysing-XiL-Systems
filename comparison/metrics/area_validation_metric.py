
from logging import getLogger
import numpy as np

from .metric_result import MetricResult
from .signal_data import SignalData
from .metric import Metric


class AreaValidationMetric(Metric):
    def __init__(self, averaging_time: float):
        super().__init__()
        self.averaging_time = averaging_time
        self.logger = getLogger(__name__)

    def __call__(self, ref_channel: SignalData, eval_channel: SignalData) -> MetricResult:

        amplitude = max(ref_channel.amplitude(), 0.00001)

        averaging_count = int(self.averaging_time /
                              ref_channel.sample_time_step)
        averaging_time = averaging_count * ref_channel.sample_time_step

        differences = np.abs(ref_channel.values -
                             eval_channel.values) / amplitude

        window = np.ones(averaging_count) / averaging_count

        averaged_differences = 1 - \
            np.convolve(differences, window, mode='same')

        averaged_differences = np.clip(averaged_differences, 0, 1)

        return MetricResult(ref_channel, eval_channel, SignalData(ref_channel.timestamps, averaged_differences), {}, {})

    def __str__(self) -> str:
        return f"AVM ({self.averaging_time})"
