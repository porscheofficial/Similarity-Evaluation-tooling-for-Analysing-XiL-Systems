from abc import ABCMeta, abstractmethod

from .signal_data import SignalData
from .metric_result import MetricResult
import numpy as np


class Metric(metaclass=ABCMeta):

    @abstractmethod
    def __call__(self, ref_channel: SignalData, eval_channel: SignalData) -> MetricResult:
        pass
