
from .metric import Metric
from .signal_data import SignalData
from .metric_result import MetricResult
from scipy.spatial.distance import cdist
import scipy.optimize as opt
import numpy as np


class OPSAMetric(Metric):
    """
    OPSA metric implementation

    Parameters:
    - cutoff: float
        Maximum distance between two points, after which the distance is clipped
    - size_y: float
        Amount to which the y-axis is scaled. The x-axis is not scaled. Default is 1 which means
        the y-axis is scaled to [1,0] making a shift of 1 second equal to a scale of 100%.
    - interval_time: float
        Length of the interval in seconds over which the metric is calculated
    - interval_extent: float
        Length of the left and right extent in seconds over which the metric is calculated
    - p: float
        Exponent of the distance calculation. Default is 1 which means the distance is the sum of
        the distances to the power of 1. The distance is then divided by the number of points in the
        evaluation channel and then the p-th root is taken. This is the final distance.
    """

    def __init__(self):
        self.cutoff = 0.5
        self.size_y = 1
        self.interval_time = 1.0
        self.interval_extent = 0.2
        self.p = 1

    def __call__(self, ref_channel: SignalData, eval_channel: SignalData) -> MetricResult:
        step = ref_channel.sample_time_step

        interval_size = int(self.interval_time / step)
        extent_size = int(self.interval_extent / step)

        ref = ref_channel.values
        eval = eval_channel.values
        time = ref_channel.timestamps

        length = len(ref)

        amplitude = ref_channel.amplitude()

        if amplitude == 0:
            amplitude = self.size_y
        else:
            ref = ref / (amplitude / self.size_y)
            eval = eval / (amplitude / self.size_y)
            amplitude = self.size_y

        ref_points = np.array([ref, time]).T
        eval_points = np.array([eval, time]).T

        result = np.zeros(length - interval_size)

        for i in range(0, length - interval_size):
            if i % 100 == 0:
                print(f"Processing {i} of {length}")
            extent_front = max(0, i - extent_size)
            extent_back = min(length - 1, i + interval_size + extent_size)
            interval_back = min(length - 1, i + interval_size)
            ref_interval = ref_points[extent_front:extent_back]
            eval_interval = eval_points[i:interval_back]
            value = self.calculate_opsa(ref_interval, eval_interval)
            result[i] = value

        result = 1 - (result / self.cutoff)
        result = SignalData(time[:-interval_size] +
                            (self.interval_time / 2), result)

        return MetricResult(ref_channel, eval_channel, result, {}, {})

    def calculate_opsa(self, ref, eval):
        n = len(ref)
        m = len(eval)
        dist_mat = cdist(eval.reshape(-1, 2),
                         ref.reshape(-1, 2), metric='euclidean')
        dist_mat = np.clip(dist_mat, 0, self.cutoff)
        dist_mat = dist_mat ** self.p

        closest_points = self.hungarian(dist_mat)

        dist = dist_mat[closest_points[0], closest_points[1]].sum()
        # dist = dist + self.cutoff ** self.p * (n - m)
        dist = dist / m
        dist = dist ** (1 / self.p)

        return dist

    def hungarian(self, dist_mat):
        row_ind, col_ind = opt.linear_sum_assignment(dist_mat)
        return np.array([row_ind, col_ind])

    def __str__(self) -> str:
        return f"OPSA ({self.cutoff}, {self.size_y}, {self.interval_time}, {self.interval_extent}, {self.p})"
