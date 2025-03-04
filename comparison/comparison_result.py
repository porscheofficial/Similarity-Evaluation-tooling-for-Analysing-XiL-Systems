import pandas as pd
import numpy as np

from logging import getLogger

from measurement.channel.channel_data import ChannelData
from .metrics import MetricResult
from .metrics.signal_data import SignalData


class ComparisonResult():
    name: str
    channel_results: list[tuple[ChannelData,
                                ChannelData, 'MetricResult']]
    result: SignalData

    def __init__(self, name: str) -> None:
        self.name = name
        self.channel_results = []

    def add_result(self, ref_channel: ChannelData, eval_channel: ChannelData, result: MetricResult) -> None:
        self.channel_results.append(
            (ref_channel, eval_channel, result))

    def calculate_total(self):
        if len(self.channel_results) == 0:
            getLogger("Comparison").warning(
                f"No results for {self.name}, cannot calculate total")
            return

        channel_results = [result for _, _, result in self.channel_results]

        all_results = np.array([result.result.values
                               for result in channel_results])
        count = all_results.shape[0]
        sum_results = np.sum(all_results, axis=0)
        combined_results = sum_results / count
        timestamps = channel_results[0].result.timestamps
        self.result = SignalData(timestamps, combined_results)

    def get_channel_result_by_name(self, name: str):
        for channel in self.channel_results:
            if channel[0].name == name:
                return channel
        return None

    @property
    def result_average(self):
        return float(self.result.values.mean())


class ChannelComparisonResult():
    name: str
    metric_used: str
    result: pd.Series
    result_median: float
    result_average: float
    result_min: float
    result_max: float
    channel1: ChannelData
    channel2: ChannelData

    def __init__(self, name: str, result: pd.Series, metric_used: str, channel1: ChannelData, channel2: ChannelData) -> None:
        self.name = name
        self.metric_used = metric_used
        self.result = result
        np_result = result.to_numpy()
        np_result = np_result.copy()
        print(np_result.shape)
        self.result_max = float(np_result.max())
        self.result_min = float(np_result.min())
        self.result_average = float(np_result.mean())
        np_result.sort()
        self.result_median = float(np_result[len(np_result) // 2])
        self.channel1 = channel1
        self.channel2 = channel2
