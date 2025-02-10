from dataclasses import dataclass
import uuid

from measurement.channel.channel import Channel


@dataclass
class Measurement:
    """
    A class to represent a measurement.

    Attributes
    ----------
    id : str
        Unique identifier for the measurement.
    name : str
        Name of the measurement.
    length : float
        Length of the measurement.
    sample_rate : float
        Sample rate of the measurement.
    channels : list[Channel]
        List of channels associated with the measurement.
    """

    id: str
    name: str
    length: float
    sample_rate: float
    channels: list[Channel]

    def add_channel(self, channel: Channel) -> None:
        """
        Add a channel to the measurement.

        Parameters
        ----------
        channel : Channel
            Channel to add to the measurement.
        """
        self.channels.append(channel)

    def get_channel_by_name(self, name: str) -> Channel:
        """
        Get a channel by its name.

        Parameters
        ----------
        name : str
            Name of the channel to retrieve.

        Returns
        -------
        Channel
            Channel with the specified name. (First found)
        """
        return next((channel for channel in self.channels if channel.name == name), None)

    def to_dict(self) -> dict:
        """
        Convert the measurement to a dictionary.

        Returns
        -------
        dict
            Dictionary representation of the measurement.
        """
        return {
            "id": self.id,
            "name": self.name,
            "length": float(self.length),
            "sample_rate": float(self.sample_rate),
            "channels": [channel.to_dict() for channel in self.channels]
        }

    @staticmethod
    def from_dict(data: dict) -> 'Measurement':
        """
        Create a measurement from a dictionary.

        Parameters
        ----------
        data : dict
            Dictionary with measurement data.

        Returns
        -------
        Measurement
            Measurement created from the dictionary.
        """
        return Measurement(data["id"], data["name"], data["length"], data["sample_rate"], [Channel.from_dict(channel) for channel in data["channels"]])
