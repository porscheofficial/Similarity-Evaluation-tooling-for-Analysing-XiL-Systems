from PySide6.QtCore import QObject
from . import *


class MetricRegistry(QObject):
    def __init__(self):
        self.metrics = {
            "ISO": IsoMetric(),
            "ISO_PHASE (0.2)": IsoPhaseMetric(),
            "ISO_PHASE (0.6)": IsoPhaseMetric(0.6),
            "ISO_CORRIDOR": IsoCorridorMetric(),
            "ISO_MAGNITUDE": IsoMagnitudeMetric(),
            "ISO_SLOPE": IsoSlopeMetric(),
            "Euclidean Distance": EuclideanDistanceMetric(),
            "Pearson Correlation": PearsonCorrelationMetric(),
            "ISO_SMALL": IsoMetricSmall(),
            "OSPAMetric": OSPAMetric(),
            "OSPAMetric (No Cutoff)": OSPAMetric(1),
            "CORRIDOR": CorridorMetric(0.05, 0.5, 0.1, 2),
            "CORRIDOR ShiftTol": CorridorMetric(0.02, 0.4, 0.07, 3.5),
        }

    def get_metric(self, name):
        return self.metrics.get(name)

    def available_metrics(self):
        return self.metrics.keys()
