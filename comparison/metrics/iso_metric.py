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


class IsoMetric(Metric):

    def __init__(self) -> None:
        super().__init__()
        self.logger = getLogger("IsoMetric")

    def __call__(self, ref_channel: SignalData, eval_channel: SignalData) -> MetricResult:
        timer = time.time()
        self.logger.info("Running IsoMetric")
        corridor_result = IsoCorridorMetric()(ref_channel, eval_channel)
        corridor_time = time.time() - timer
        magnitude_result = IsoMagnitudeMetric()(ref_channel, eval_channel)
        magnitude_time = time.time() - corridor_time - timer
        phase_result = IsoPhaseMetric()(ref_channel, eval_channel)
        phase_time = time.time() - magnitude_time - corridor_time - timer
        slope_result = IsoSlopeMetric()(ref_channel, eval_channel)
        slope_time = time.time() - phase_time - magnitude_time - corridor_time - timer
        self.logger.info(
            f"Partial results calculated ({corridor_time:.1f}s, {magnitude_time:.1f}s, {phase_time:.1f}s, {slope_time:.1f}s)")

        total_result = corridor_result.result * 0.4 + magnitude_result.result * \
            0.2 + phase_result.result * 0.2 + slope_result.result * 0.2

        combined_metadata = {}
        combined_metadata.update(corridor_result.input_metadata)
        combined_metadata.update(magnitude_result.input_metadata)
        combined_metadata.update(phase_result.input_metadata)
        combined_metadata.update(slope_result.input_metadata)

        result = MetricResult(ref_channel, eval_channel, total_result, {
            "corridor": corridor_result.result,
            "magnitude": magnitude_result.result,
            "phase": phase_result.result,
            "slope": slope_result.result
        }, combined_metadata)

        return result

    def __str__(self) -> str:
        return "ISO Metric"
