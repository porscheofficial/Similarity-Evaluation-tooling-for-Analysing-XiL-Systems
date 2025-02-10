import numpy as np

from dataclasses import dataclass

from measurement.channel.channel_data import ChannelData


@dataclass
class SignalData:
    timestamps: np.ndarray
    values: np.ndarray

    def __len__(self):
        return len(self.values)

    def __getitem__(self, key) -> tuple[float, float]:
        return (self.values[key], self.timestamps[key])

    def amplitude(self) -> float:
        return max(abs(np.max(self.values)), abs(np.min(self.values)))

    def __mul__(self, other: float | int) -> 'SignalData':
        return SignalData(self.timestamps, self.values * other)

    def __add__(self, other: 'SignalData') -> 'SignalData':
        return SignalData(self.timestamps, self.values + other.values)

    def min(self) -> float:
        return np.min(self.values)

    def max(self) -> float:
        return np.max(self.values)

    def mean(self) -> float:
        return np.mean(self.values)

    @property
    def shape(self):
        return self.values.shape

    @property
    def sample_time_step(self):
        return self.timestamps[1] - self.timestamps[0]

    @staticmethod
    def from_channel_data(data: ChannelData) -> 'SignalData':
        return SignalData(data.timestamps(), data.datapoints())

    @staticmethod
    def empty() -> 'SignalData':
        return SignalData(np.array([]), np.array([]))
