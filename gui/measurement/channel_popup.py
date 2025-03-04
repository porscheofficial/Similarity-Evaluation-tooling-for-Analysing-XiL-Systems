import logging
from PySide6 import QtCore, QtWidgets, QtGui

from gui.plot_widget import PlotWidget

import matplotlib.pyplot as plt

from measurement.channel.channel import Channel
from measurement.channel.channel_data_repository import ChannelDataRepository
from measurement.channel.channel_processor import ChannelProcessor

import gui.utils as utils

import os
import pandas as pd
import numpy as np

from measurement.channel.channel_repository import ChannelRepository


class ChannelPopup(QtWidgets.QWidget):
    def __init__(self, channel: Channel):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.channel = channel
        self.data = ChannelDataRepository().load_from_channel(channel)
        self.setWindowTitle("Signal Popup")
        self.resize(400, 300)

        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # Create a label to display the channel name
        channel_label = QtWidgets.QLabel(self.channel.name)
        layout.addWidget(channel_label)

        plot_widget = PlotWidget()
        plot_widget.setMinimumSize(300, 400)
        plot_widget.plot_channel_data(self.data)
        layout.addWidget(plot_widget)

        show_description_button = QtWidgets.QPushButton("Show Description")
        show_description_button.clicked.connect(self.show_description)
        layout.addWidget(show_description_button)

        layout.addWidget(QtWidgets.QLabel("Found in:"))
        aliases = QtWidgets.QListWidget()
        aliases.setFixedHeight(100)
        repo = ChannelRepository()
        for alias in self.channel.aliases:
            if not repo.is_name_qualified(alias):
                continue
            pdu = repo.get_pdu_name(alias)
            bus = repo.get_bus_name(alias)
            text = f"PDU: {pdu}, Bus: {bus}"
            aliases.addItem(text)
        layout.addWidget(aliases)

        mapping_grid = QtWidgets.QGridLayout()

        mapping_grid.addWidget(QtWidgets.QLabel("Value"), 0, 0)
        mapping_grid.addWidget(QtWidgets.QLabel("Meaning"), 0, 1)

        for i, (key, value) in enumerate(self.channel.value_name_mapping.items()):
            key_label = QtWidgets.QLabel(f"{key}")
            value_label = QtWidgets.QLabel(f"{value}")

            mapping_grid.addWidget(key_label, i+1, 0)
            mapping_grid.addWidget(value_label, i+1, 1)

        layout.addLayout(mapping_grid)

        # Create a button to show the plot of the signal
        scale_button = QtWidgets.QPushButton("Scale")
        scale_button.clicked.connect(self.scale_data)
        layout.addWidget(scale_button)

        shift_button = QtWidgets.QPushButton("Shift")
        shift_button.clicked.connect(self.shift_data)
        layout.addWidget(shift_button)

        utils.update_layout(self, layout)

    def scale_data(self):
        amount, ok = QtWidgets.QInputDialog.getDouble(
            self, "Scale", "Amount:", value=1, minValue=0.01)

        processor = ChannelProcessor()
        repository = ChannelDataRepository()
        if ok:
            self.logger.info(f"Scaling data by {amount}")
            self.data = processor.scale(self.data, amount)
            repository.store(self.data)
            self.setup_ui()

    def shift_data(self):
        amount, ok = QtWidgets.QInputDialog.getDouble(
            self, "Shift", "Amount (s):", value=0, decimals=2)

        processor = ChannelProcessor()
        repository = ChannelDataRepository()
        if ok:
            self.logger.info(f"Shifting data by {amount}")
            self.data = processor.shift_data(self.data, amount)
            repository.store(self.data)
            self.setup_ui()

    def show_description(self):
        repo = ChannelRepository()
        description = repo.get_channel_description(self.channel)
        if description is not None:
            QtWidgets.QMessageBox.information(self, "Description", description)
        else:
            QtWidgets.QMessageBox.warning(
                self, "Warning", "Description not found.")
