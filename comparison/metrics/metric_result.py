from dataclasses import dataclass
from .signal_data import SignalData
import numpy as np


@dataclass
class MetricResult:
    reference_input: SignalData
    evaluated_input: SignalData
    result: SignalData
    result_metadata: dict[str, SignalData]
    input_metadata: dict[str, SignalData]

    @staticmethod
    def merge(a: 'MetricResult', b: 'MetricResult', result: SignalData) -> 'MetricResult':
        return MetricResult(
            a.reference_input,
            a.evaluated_input,
            result,
            {**a.result_metadata, **b.result_metadata},
            {**a.input_metadata, **b.input_metadata}
        )
