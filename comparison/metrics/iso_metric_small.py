from measurement.channel.channel_data import ChannelData
from .signal_data import SignalData
from .metric import Metric
from .iso_corridor_metric import IsoCorridorMetric
from .iso_magnitude_metric import IsoMagnitudeMetric
from .iso_phase_metric import IsoPhaseMetric
from .iso_slope_metric import IsoSlopeMetric
from .metric_result import MetricResult
from logging import getLogger

import time


import pandas as pd
import numpy as np


class IsoMetricSmall(Metric):

    def __init__(self, allowed_time_shift: float = 0.3) -> None:
        super().__init__()
        self.logger = getLogger("IsoMetric")
        self.allowed_time_shift = allowed_time_shift

    def __call__(self, ref_channel: SignalData, eval_channel: SignalData) -> MetricResult:
        timer = time.time()
        corridor_result = IsoCorridorMetric()(ref_channel, eval_channel)
        phase_result = IsoPhaseMetric(
            self.allowed_time_shift)(ref_channel, eval_channel)

        total_result = corridor_result.result * 0.5 + phase_result.result * 0.5

        combined_metadata = {}
        combined_metadata.update(corridor_result.input_metadata)
        combined_metadata.update(phase_result.input_metadata)

        result = MetricResult(ref_channel, eval_channel, total_result, {
            "corridor": corridor_result.result,
            "phase": phase_result.result,
        }, combined_metadata)

        return result

    def __str__(self) -> str:
        return f"IsoMetricSmall ({self.allowed_time_shift})"
