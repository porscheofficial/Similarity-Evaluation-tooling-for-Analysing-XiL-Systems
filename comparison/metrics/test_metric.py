"""from channel_data import ChannelData
from metrics.metric import Metric
from logging import getLogger

from comparison_result import ChannelComparisonResult
import pandas as pd
import numpy as np


class TestMetric(Metric):

    def __call__(self, channel_a: ChannelData, channel_b: ChannelData, sample_rate: float) -> ChannelComparisonResult:
        logger = getLogger("Metric")
        timestamps_a = channel_a.timestamps()
        timestamps_b = channel_b.timestamps()
        values_a = channel_a.datapoints()
        values_b = channel_b.datapoints()
        index_b = 0
        index_a = 0

        logger.warning(
            "Sync time not implemented, using shorter measurement as reference")

        start_time = max(timestamps_a[0], timestamps_b[0])
        end_time = min(timestamps_a[-1], timestamps_b[-1])

        logger.info("Comparing channels")

        timestamps = np.arange(start_time, end_time, 1/sample_rate)
        datapoints = np.zeros(len(timestamps))

        for i, time in enumerate(timestamps):
            while index_a + 1 < len(timestamps_a) and timestamps_a[index_a + 1] < time:
                index_a += 1
            while index_b + 1 < len(timestamps_b) and timestamps_b[index_b + 1] < time:
                index_b += 1
            if index_a >= len(timestamps_a) or index_b >= len(timestamps_b):
                break
            current = abs(float(values_a[index_a]) - float(values_b[index_b]))
            datapoints[i] = current

        series = pd.Series(index=timestamps, data=datapoints)

        result = ChannelComparisonResult(
            f"{channel_a.name} vs {channel_b.name}", series, "TestMetric", channel_a, channel_b)

        logger.info(f"Comparison done ({channel_a.name} vs {channel_b.name})")
        return result"""
