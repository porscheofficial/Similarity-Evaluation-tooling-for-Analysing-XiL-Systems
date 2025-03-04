

from measurement.channel.channel_data import ChannelData

import numpy as np


class ChannelProcessor():

    def resample(self, channel_data: ChannelData, length: float, samples: int) -> ChannelData:
        """
        Resamples the given channel data to a specified length and number of samples.
        Args:
            channel_data (ChannelData): The original channel data to be resampled.
            length (float): The desired length of the resampled data.
            samples (int): The number of samples in the resampled data.
        Returns:
            ChannelData: The resampled channel data.
        """
        timestamps = np.linspace(0, length, samples)
        values = np.zeros(len(timestamps))

        old_timestamps = channel_data.timestamps()
        old_values = channel_data.datapoints()
        old_index = 0

        for index, time in enumerate(timestamps):
            while time > old_timestamps[old_index] and old_index < len(old_timestamps) - 1:
                old_index += 1
            values[index] = old_values[old_index]

        return ChannelData(timestamps, values, channel_data.name, channel_data.id)

    def normalize_channel(self, channel_data: ChannelData, length: float, sample_rate: float) -> ChannelData:
        """
        Normalize the channel data to a specific length and sample rate.

        Therefore in the new ChannelData at each timestamp the value of the next timestamp of the original data is taken.

        Parameters
        ----------
        channel_data : ChannelData
            Channel data to normalize.
        length : float
            Length to normalize the channel data to.
        sample_rate : float
            Sample rate to normalize the channel data to.

        Returns
        -------
        ChannelData
            Normalized channel data.
        """
        num_samples = int(length * sample_rate)
        return self.resample(channel_data, length, num_samples)

    def apply_sync(self, channel_data: ChannelData, sync_start_time: float, sync_end_time: float) -> ChannelData:
        """
        Apply a sync to the channel data.

        The sync is applied by subtracting the sync start time from the timestamps of the channel data.

        Parameters
        ----------
        channel_data : ChannelData
            Channel data to apply the sync to.
        sync_start_time : float
            Start time of the sync.
        sync_end_time : float
            End time of the sync.

        Returns
        -------
        ChannelData
            Channel data with applied sync.
        """
        old_data = np.concatenate((channel_data.timestamps(
        ).reshape(-1, 1), channel_data.datapoints().reshape(-1, 1)), axis=1)
        new_data = old_data[(old_data[:, 0] >= sync_start_time) &
                            (old_data[:, 0] <= sync_end_time)]
        new_index = new_data[:, 0] - sync_start_time
        new_values = new_data[:, 1]
        return ChannelData(new_index, new_values, channel_data.name, channel_data.id)

    def scale(self, channel_data: ChannelData, factor: float) -> ChannelData:
        """
        Scales the channel data by a factor.

        Parameters
        ----------
        channel_data : ChannelData
            Channel data to scale.
        factor : float
            Factor to scale the channel data by.

        Returns
        -------
        ChannelData
            Scaled channel data.
        """
        return ChannelData(channel_data.timestamps(), channel_data.datapoints() * factor, channel_data.name, channel_data.id)

    def shift_data(self, channel_data: ChannelData, shift: float) -> ChannelData:
        """
        Shifts the channel data by a specific amount.
        Requires the channel data to be normalized.

        Parameters
        ----------
        channel_data : ChannelData
            Channel data to shift.
        shift : float
            Amount to shift the channel data by.

        Returns
        -------
        ChannelData
            Shifted channel data.
        """

        shifted = ChannelData(channel_data.timestamps(
        ) + shift, channel_data.datapoints(), channel_data.name, channel_data.id)

        sample_delta = channel_data.timestamps()[1]
        length = channel_data.timestamps()[-1] + sample_delta

        normalized = self.normalize_channel(
            shifted, length, 1/sample_delta)

        return normalized
