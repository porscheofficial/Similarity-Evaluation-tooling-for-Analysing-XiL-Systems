import numpy as np

from measurement.channel.channel import Channel
from measurement.channel.channel_data import ChannelData
from measurement.channel.channel_data_repository import ChannelDataRepository
from measurement.channel.channel_repository import ChannelRepository
from measurement.measurement import Measurement

from scipy.signal import sawtooth, square


class ChannelGenerator:

    def __init__(self) -> None:
        self.data_repo = ChannelDataRepository()
        self.repo = ChannelRepository()

    def generate_channel(self, x, y, name, measurement: Measurement) -> ChannelData:
        if len(measurement.channels) != 0:
            group_id = self.repo.parse_group_id(measurement.channels[-1].id)
        else:
            group_id = self.repo.generate_group_id()

        channel_id = self.repo.generate_channel_id(group_id)

        return ChannelData(x, y, name, channel_id)

    def generate_sinus(self, scale, offset, stretch, name: str, measurement: Measurement) -> ChannelData:
        """
        Generates a sinusoidal channel data.

        Args:
            scale (float): Amplitude of the sinusoidal wave.
            offset (float): Phase shift of the sinusoidal wave.
            stretch (float): Frequency multiplier of the sinusoidal wave.
            name (str): Name of the channel.
            measurement (Measurement): Measurement object containing sample rate information.

        Returns:
            ChannelData: Generated channel data with sinusoidal wave.
        """
        sample_rate = int(measurement.sample_rate)
        x = np.linspace(0, 10, sample_rate * 10)
        y = (np.sin(2 * np.pi * (x - offset) * stretch) + 1) * scale / 2
        return self.generate_channel(x, y, name, measurement)

    def generate_gaussian_curve(self, scale, offset, stretch, name: str, measurement: Measurement) -> ChannelData:
        """
        Generates a Gaussian curve based on the provided parameters and measurement data.
        Parameters:
        - scale (float): The amplitude of the Gaussian curve.
        - offset (float): The horizontal shift of the Gaussian curve.
        - stretch (float): The standard deviation (spread) of the Gaussian curve.
        - name (str): The name of the channel.
        - measurement (Measurement): An object containing measurement data, specifically the sample rate.
        Returns:
        - ChannelData: The generated channel data containing the Gaussian curve.
        The measurement is used to determine the sample rate, which affects the resolution of the generated Gaussian curve.
        """
        sample_rate = int(measurement.sample_rate)
        x = np.linspace(0, 10, sample_rate * 10)
        y = scale * np.exp(-((x - 5 - offset) ** 2) / (2 * stretch ** 2))
        return self.generate_channel(x, y, name, measurement)

    def generate_square_wave(self, scale, offset, stretch, name: str, measurement: Measurement) -> ChannelData:
        """
        Generates a square wave signal and returns it as ChannelData.

        Parameters:
        scale (float): The amplitude of the square wave.
        offset (float): The phase offset of the square wave.
        stretch (float): The frequency stretch factor of the square wave.
        name (str): The name of the channel.
        measurement (Measurement): The measurement object containing sample rate information.

        Returns:
        ChannelData: The generated square wave signal as ChannelData.
        """
        sample_freq = int(measurement.sample_rate)
        sample_rate = 1 / sample_freq
        x = np.linspace(0, 10, sample_freq * 10)
        y = (square(2 * np.pi * (x - offset) * stretch * (10/(10+sample_rate))) + 1) * scale / 2
        return self.generate_channel(x, y, name, measurement)

    def generate_block(self, scale, offset, stretch, name: str, measurement: Measurement) -> ChannelData:
        """
        Generates a block of channel data based on the given parameters.

        Args:
            scale (float): The scale factor to apply to the y-values.
            offset (float): The offset to apply to the x-values before stretching.
            stretch (float): The factor by which to stretch the x-values.
            name (str): The name of the channel.
            measurement (Measurement): The measurement object containing sample rate and other metadata.

        Returns:
            ChannelData: The generated channel data.
        """
        sample_rate = int(measurement.sample_rate)
        x = np.linspace(0, 10, sample_rate * 10)
        y = np.zeros_like(x)
        changed_x = (x - offset) * stretch - ((5 * stretch) - 5)
        y[(changed_x >= 3) & (changed_x <= 7)] = scale
        return self.generate_channel(x, y, name, measurement)

    def generate_sawtooth_wave(self, scale, offset, stretch, name: str, measurement: Measurement) -> ChannelData:
        """
        Generates a sawtooth wave and returns it as ChannelData.

        Parameters:
        scale (float): The amplitude scaling factor for the sawtooth wave.
        offset (float): The phase offset for the sawtooth wave.
        stretch (float): The frequency stretch factor for the sawtooth wave.
        name (str): The name of the channel.
        measurement (Measurement): The measurement object containing sample rate information.

        Returns:
        ChannelData: The generated sawtooth wave data encapsulated in a ChannelData object.
        """
        sample_rate = int(measurement.sample_rate)
        x = np.linspace(0, 10, sample_rate * 10)
        y = (sawtooth(2 * np.pi * (x - offset) * stretch, 0.8) + 1) * scale / 2
        return self.generate_channel(x, y, name, measurement)

    def generate_dirac_impulse(self, scale, offset, stretch, name: str, measurement: Measurement) -> ChannelData:
        """
        Generates a Dirac impulse signal and returns it as ChannelData.

        Parameters:
        scale (float): The amplitude scaling factor for the Dirac impulse.
        offset (float): The phase offset for the Dirac impulse.
        stretch (float): The frequency stretch factor for the Dirac impulse.
        name (str): The name of the channel.
        measurement (Measurement): The measurement object containing sample rate information.

        Returns:
        ChannelData: The generated Dirac impulse signal as ChannelData.
        """
        sample_rate = int(measurement.sample_rate)
        x = np.linspace(0, 10, sample_rate * 10)
        y = np.zeros_like(x)
        y[int(sample_rate * (5-offset))] = scale
        return self.generate_channel(x, y, name, measurement)
