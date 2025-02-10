
import json
import os
import pandas as pd
import uuid

from logging import getLogger

from .channel import Channel


class ChannelRepository():

    def __init__(self) -> None:
        self.logger = getLogger(__name__)
        self.storage_folder = os.getcwd() + "/measurements" + "/channels"
        if not os.path.exists(self.storage_folder):
            os.makedirs(self.storage_folder)

    def store(self, channel: Channel) -> None:
        group_id = channel.id.split(".")[0]
        filename = self.storage_folder + "/" + group_id + ".json"
        dict_to_store = channel.__dict__.copy()
        dict_to_store.pop("value_name_mapping")
        dict_to_store["value_name_mapping"] = {}
        for value, name in channel.value_name_mapping.items():
            dict_to_store["value_name_mapping"] = {
                **dict_to_store["value_name_mapping"], str(name): float(value)}

        group_data = {}
        if os.path.exists(filename):
            group_data = json.load(open(filename, "r"))
        else:
            self.logger.info(
                f"Group {group_id} does not exist yet. Creating...")

        group_data[channel.id] = dict_to_store

        json.dump(group_data, open(filename, "w"))

        # self.logger.info(f"Stored channel {channel.name} with id {channel.id}")

    def load(self, id: str) -> Channel:
        group_id = id.split(".")[0]
        filename = self.storage_folder + "/" + group_id + ".json"

        if not os.path.exists(filename):
            self.logger.error(f"Could not find group with id {group_id}")
            return None

        group_dict = json.load(open(filename))

        channel_dict = group_dict[id]

        value_name_mapping = channel_dict["value_name_mapping"]
        new_value_name_mapping = {}
        for value, name in value_name_mapping.items():
            new_value_name_mapping[float(value)] = name

        return Channel(channel_dict["id"], channel_dict["name"], channel_dict["aliases"], new_value_name_mapping)

    def store_group(self, group_id: str, data: list[Channel]):
        filename = self.storage_folder + "/" + group_id + ".json"

        group_data = {}
        if os.path.exists(filename):
            group_data = json.load(open(filename, "r"))
        else:
            self.logger.info(
                f"Group {group_id} does not exist yet. Creating...")

        for channel in data:
            dict_to_store = channel.__dict__.copy()
            dict_to_store.pop("value_name_mapping")
            dict_to_store["value_name_mapping"] = {}
            for value, name in channel.value_name_mapping.items():
                dict_to_store["value_name_mapping"] = {
                    **dict_to_store["value_name_mapping"], str(name): float(value)}

            group_data[channel.id] = dict_to_store

        json.dump(group_data, open(filename, "w"))

    def delete_group(self, group_id: str):
        filename = self.storage_folder + "/" + group_id + ".json"
        if os.path.exists(filename):
            os.remove(filename)
        else:
            self.logger.error(f"Could not find group with id {group_id}")

    def generate_group_id(self) -> str:
        return str(uuid.uuid4())

    def generate_channel_id(self, group_id: str) -> str:
        channel_id = str(uuid.uuid4())
        return f"{group_id}.{channel_id}"

    def parse_group_id(self, channel_id: str) -> str:
        return channel_id.split(".")[0]

    def parse_channel_id(self, channel_id: str) -> str:
        return channel_id.split(".")[1]

    def is_name_qualified(self, channel: Channel | str) -> bool:
        if isinstance(channel, Channel):
            name = channel.name
        else:
            name = channel
        if len(name.split("::")) != 3:
            return False
        last_name = name.split("::")[-1]
        if "XIX" not in last_name:
            return False
        return True

    def get_signal_name(self, channel: Channel | str) -> str:
        if isinstance(channel, Channel):
            name = channel.name
        else:
            name = channel
        last = name.split("::")[-1]
        return last.split("_XIX")[0]

    def get_bus_name(self, channel: Channel | str) -> str:
        if isinstance(channel, Channel):
            name = channel.name
        else:
            name = channel
        last = name.split("::")[-1]
        return last.split("XIX_")[-1]

    def get_pdu_name(self, channel: Channel | str) -> str:
        if isinstance(channel, Channel):
            name = channel.name
        else:
            name = channel
        last = name.split("::")[-1]
        return last.split("_XIX_")[1]

    def get_channel_description(self, channel: Channel | str) -> str | None:
        bus_name = self.get_bus_name(channel)
        signal_name = self.get_signal_name(channel)

        file = os.getcwd() + "/kmatrix/kmatrix.csv"

        if not os.path.exists(file):
            self.logger.error("Kmatrix file not found.")
            return None

        kmatrix = pd.read_csv(os.getcwd() + "/kmatrix/kmatrix.csv", sep=';')
        kmatrix = kmatrix.applymap(
            lambda x: x.strip() if isinstance(x, str) else x)

        entry = kmatrix[(kmatrix['Bus'] == bus_name) &
                        (kmatrix['Signal'] == signal_name)]
        if not entry.empty:
            description = entry.iloc[0]['Description']
            return description
        else:
            return None
