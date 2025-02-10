

import json
from logging import getLogger
import os

from measurement.channel.channel import Channel

from .channel_data import ChannelData

import pandas as pd


class ChannelDataRepository():

    def __init__(self) -> None:
        self.logger = getLogger(__name__)
        self.storage_folder = os.getcwd() + "/measurements" + "/channel_data"

        self.cache = {}
        self.metadata_cache = {}

        self.hit_count = 0
        self.miss_count = 0

        if not os.path.exists(self.storage_folder):
            os.makedirs(self.storage_folder)

    def store(self, channel_data: ChannelData) -> None:
        group_id = channel_data.id.split(".")[0]
        filename = self.storage_folder + "/" + group_id + ".parquet"
        metadata_filename = self.storage_folder + \
            "/" + group_id + "_metadata.json"

        dataframe = pd.DataFrame()
        group_metadata = {}
        if os.path.exists(filename):
            dataframe = pd.read_parquet(filename)
            group_metadata = json.load(open(metadata_filename, "r"))
        else:
            self.logger.info(
                f"Could not find channel data group {group_id}, creating it")

        dataframe[f"{channel_data.id} time"] = channel_data.timestamps()
        dataframe[f"{channel_data.id} value"] = channel_data.datapoints()
        dataframe.to_parquet(filename)
        group_metadata[f"{channel_data.id}"] = {
            "name": channel_data.name,
            "id": channel_data.id
        }

        json.dump(group_metadata, open(metadata_filename, "w"))

        # self.logger.info(
        #    f"Stored channel data {channel_data.name} with id {channel_data.id}")

    def load(self, id: str) -> ChannelData:
        group_id = id.split(".")[0]

        if group_id in self.cache and group_id in self.metadata_cache:
            dataframe = self.cache[group_id]
            group_metadata = self.metadata_cache[group_id]
            self.hit_count += 1
        else:
            filename = self.storage_folder + "/" + group_id + ".parquet"
            metadata_filename = self.storage_folder + \
                "/" + group_id + "_metadata.json"

            if not os.path.exists(filename) or not os.path.exists(metadata_filename):
                self.logger.error(f"Could not find channel data with id {id}")
                return None

            group_metadata = json.load(open(metadata_filename))
            dataframe = pd.read_parquet(filename)

            self.cache[group_id] = dataframe
            self.metadata_cache[group_id] = group_metadata

            if len(self.cache) > 10:
                first_item = next(iter(self.cache))
                self.cache.pop(first_item)
                first_item = next(iter(self.metadata_cache))
                self.metadata_cache.pop(first_item)

            self.miss_count += 1

        metadata = group_metadata[id]
        time = dataframe[f"{id} time"].to_numpy()
        values = dataframe[f"{id} value"].to_numpy()

        if self.hit_count + self.miss_count % 100 == 0:
            self.logger.info(
                f"Current hit rate {self.hit_count / (self.hit_count + self.miss_count):.2f}")

        return ChannelData(time, values, metadata["name"], metadata["id"])

    def load_from_channel(self, channel: Channel) -> ChannelData:
        return self.load(channel.id)

    def store_group(self, group_id: str, data: list[ChannelData]):
        filename = self.storage_folder + "/" + group_id + ".parquet"
        metadata_filename = self.storage_folder + \
            "/" + group_id + "_metadata.json"

        dataframe = pd.DataFrame()
        group_metadata = {}
        if os.path.exists(filename):
            self.logger.error(
                f"Channel Data Group {group_id} already exists, cannot store an existing group")
            return

        dataframe_headers = []
        dataframe_columns = []
        for channel_data in data:
            dataframe_headers.append(f"{channel_data.id} time")
            dataframe_headers.append(f"{channel_data.id} value")
            dataframe_columns.append(channel_data.timestamps())
            dataframe_columns.append(channel_data.datapoints())
            group_metadata[f"{channel_data.id}"] = {
                "name": channel_data.name,
                "id": channel_data.id
            }

        new_dataframe = pd.DataFrame(
            dict(zip(dataframe_headers, dataframe_columns)))

        dataframe = pd.concat([dataframe, new_dataframe], axis=1)

        dataframe.to_parquet(filename)
        json.dump(group_metadata, open(metadata_filename, "w"))

    def delete_group(self, group_id: str):
        filename = self.storage_folder + "/" + group_id + ".parquet"
        metadata_filename = self.storage_folder + \
            "/" + group_id + "_metadata.json"

        if os.path.exists(filename):
            os.remove(filename)
            self.logger.info(f"Deleted channel data group {group_id}")
        else:
            self.logger.error(
                f"Could not find channel data group {group_id} to delete")
            return

        if os.path.exists(metadata_filename):
            os.remove(metadata_filename)
        else:
            self.logger.error(
                f"Could not find metadata for channel data group {group_id} to delete")
            return
