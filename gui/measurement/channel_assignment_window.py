from logging import getLogger
from PySide6 import QtCore, QtWidgets
from gui import utils
from gui.plot_widget import PlotWidget
from measurement.channel.channel_data_repository import ChannelDataRepository
from measurement.measurement import Measurement
from measurement.measurement_registry import MeasurementRegistry

import pandas as pd
import time


class ChannelAssignmentWindow(QtWidgets.QWidget):
    comparison_complete = QtCore.Signal(list)

    def __init__(self, measurement: Measurement):
        super().__init__()
        self.logger = getLogger(__name__)
        self.measurement = measurement
        self.channel_index = 0
        self.matches = []
        self.channel_mapping = []
        self.current_channel = None
        self.selected_channel = None
        self.repository = ChannelDataRepository()
        self.selected_measurement = None
        self.comparison_started = False

        self.update_ui()

    def update_ui(self):
        if self.layout() is None:
            self.init_ui()

        self.plot_widget.canvas.ax.clear()

        if self.current_channel is None and self.selected_channel is None:
            self.plot_widget.hide()
        else:
            self.plot_widget.show()

        if self.current_channel is not None:
            self.plot_widget.plot_channel_data(self.current_channel, color=0)
        if self.selected_channel is not None:
            self.plot_widget.plot_channel_data(self.selected_channel, color=1)

        self.list_widget.clear()
        if len(self.matches) != 0:
            self.list_widget.addItems(self.matches)

    def init_ui(self):
        self.setWindowTitle("Channel Mapping Window")
        self.setGeometry(100, 100, 800, 600)

        layout = QtWidgets.QVBoxLayout()

        self.measurement_combo = QtWidgets.QComboBox()
        self.measurement_combo.addItem("Select Measurement")
        for measurement in MeasurementRegistry().measurements:
            self.measurement_combo.addItem(measurement.name)
        self.measurement_combo.currentTextChanged.connect(
            self.handle_measurement_selected)
        layout.addWidget(self.measurement_combo)

        self.plot_widget = PlotWidget()
        self.plot_widget.setFixedSize(450, 250)

        layout.addWidget(self.plot_widget)

        self.channel_name_label = QtWidgets.QLabel("Channel Name")
        layout.addWidget(self.channel_name_label)
        self.channel_name_input = QtWidgets.QLineEdit()
        self.channel_name_input.setPlaceholderText("Channel Name")
        self.channel_name_input.editingFinished.connect(self.search_channels)
        layout.addWidget(self.channel_name_input)

        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.itemDoubleClicked.connect(
            self.handle_channel_selected)
        self.list_widget.setFixedHeight(400)

        layout.addWidget(self.list_widget)

        actions_layout = QtWidgets.QHBoxLayout()

        use_button = QtWidgets.QPushButton("Use Selected Channel")
        use_button.clicked.connect(self.handle_use_channel)
        actions_layout.addWidget(use_button)

        skip_button = QtWidgets.QPushButton("Skip Channel")
        skip_button.clicked.connect(self.handle_skip_channel)
        actions_layout.addWidget(skip_button)

        layout.addLayout(actions_layout)

        utils.update_layout(self, layout)

    def handle_measurement_selected(self, measurement_name):
        if self.comparison_started:
            return
        if measurement_name == "Select Measurement":
            return
        self.selected_measurement = MeasurementRegistry().get_by_name(measurement_name)
        self.comparison_started = True
        self.measurement_combo.setEnabled(False)
        self.compare_channels()

    def compare_channels(self):
        if self.selected_measurement is None or self.channel_index >= len(self.measurement.channels):
            self.comparison_complete.emit(self.channel_mapping)
            self.save_channel_mapping()
            btn = QtWidgets.QMessageBox.information(
                self, "Channel Comparison", "Comparison Complete")
            return

        current_channel = self.measurement.channels[self.channel_index]
        self.current_channel = self.repository.load_from_channel(
            current_channel)
        self.channel_name_label.setText(
            f"Channel Name: {current_channel.name}")
        self.channel_name_input.setText(current_channel.name)

        self.search_channels()

    def search_channels(self):
        name = self.channel_name_input.text().lower()

        search_terms = name.split(" ")
        matches_list = []
        for channel in self.selected_measurement.channels:
            for channel_name in channel.aliases:
                channel_name = channel_name.lower()
                similarity = 0
                matches = True
                for term in search_terms:
                    if term not in channel_name:
                        matches = False
                        break
                if matches:
                    matches_list.append(channel.name)
                    break

        self.matches = matches_list
        self.update_ui()

    def handle_channel_selected(self, item):
        selected_channel_name = item.text()

        selected_channel = self.selected_measurement.get_channel_by_name(
            selected_channel_name)

        self.selected_channel = self.repository.load_from_channel(
            selected_channel)

        self.update_ui()

    def handle_use_channel(self):
        if self.current_channel is None:
            return
        if self.selected_channel is None:
            return
        self.channel_mapping.append(
            (self.current_channel.name, self.selected_channel.name))
        self.channel_index += 1
        self.compare_channels()

    def handle_skip_channel(self):
        self.channel_index += 1
        self.compare_channels()

    def save_channel_mapping(self):
        saved_mapping = pd.DataFrame(columns=["Channel", "Mapped Channel"])
        for mapping in self.channel_mapping:
            saved_mapping = saved_mapping.add(
                {"Channel": mapping[0], "Mapped Channel": mapping[1]})
        filename = f"channel_mapping_{time.time()}.csv"
        saved_mapping.to_csv(filename, index=False)
