from typing import Any
import pandas as pd

from logging import getLogger

import numpy as np


class ChannelData():

    def __init__(self, timestamps: np.ndarray, values: np.ndarray, name: str, id: str) -> None:
        self.index = timestamps
        self.values = values
        self.name = name
        self.id = id
        self.logger = getLogger(__name__)

    def timestamps(self) -> np.ndarray:
        return self.index

    def datapoints(self) -> np.ndarray:
        return self.values

    def __call__(self, time) -> Any:
        index = 0
        step_size = len(self.index) // 2
        while True:
            time_at_index = self.index[index]
            time_at_next_index = self.index[index + 1]

            if time_at_index <= time <= time_at_next_index:
                return self.values[index]

            if time < time_at_index:
                index -= step_size
            else:
                index += step_size

            if index < 0:
                self.logger.error(
                    f"Time {time} is before the first timestamp {self.index[0]}")
                return 0
            if index >= len(self.index):
                self.logger.error(
                    f"Time {time} is after the last timestamp {self.index[-1]}")
                return 0

            step_size = max(step_size // 2, 1)

    @property
    def length_seconds(self) -> float:
        return self.index[-1] - self.index[0]

    @property
    def length_samples(self) -> int:
        return len(self.index)

    def min(self) -> float:
        return float(self.values.min())

    def max(self) -> float:
        return float(self.values.max())

    def to_numpy(self) -> np.ndarray:
        """
        Convert the channel data to a NumPy array.

        Returns:
            np.ndarray: A NumPy array containing the channel index and values.
        """
        return np.array([self.index, self.values])
