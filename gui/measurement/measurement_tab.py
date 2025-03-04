from PySide6 import QtCore, QtWidgets, QtGui

from comparison.comparison import Comparison
from gui.measurement.channel_assignment_window import ChannelAssignmentWindow
from gui.measurement.channel_popup import ChannelPopup
from gui.comparison.compare_tab import CompareTab
from gui.main_view import MainView
from gui.measurement.new_channel_window import NewChannelWindow
from measurement.channel.channel_repository import ChannelRepository
from measurement.measurement import Measurement
from measurement.measurement_registry import MeasurementRegistry

import gui.utils as utils


class MeasurementTab(QtWidgets.QWidget):
    def __init__(self, measurement: Measurement) -> None:
        super().__init__()
        self.measurement = measurement
        self.registry = MeasurementRegistry()
        self.init_ui()

    def init_ui(self):

        self.main_layout = QtWidgets.QVBoxLayout()
        self.title = QtWidgets.QLabel(f"Measurement: {self.measurement.name}")
        self.title.setStyleSheet("font-size: 20px")
        self.main_layout.addWidget(self.title)

        actions_layout = QtWidgets.QHBoxLayout()

        compare_button = QtWidgets.QPushButton("Compare")
        compare_button.clicked.connect(self.handle_compare)
        rename_button = QtWidgets.QPushButton("Rename")
        rename_button.clicked.connect(self.handle_rename)

        toolbar = QtWidgets.QToolBar()

        toolbar.addAction("Compare", self.handle_compare)
        toolbar.addAction("Rename", self.handle_rename)
        toolbar.addAction("Delete", self.delete_measurement)
        toolbar.addAction("Create Mapping", self.create_mapping)
        toolbar.addAction("Add Signal", self.add_channel)

        actions_layout.addWidget(toolbar)

        self.main_layout.addLayout(actions_layout)
        self.main_layout.addWidget(QtWidgets.QLabel(
            f"Sample Rate: {self.measurement.sample_rate} Hz"))
        self.main_layout.addWidget(QtWidgets.QLabel(
            f"Signals: {len(self.measurement.channels)}"))
        self.main_layout.addWidget(QtWidgets.QLabel(
            f"Duration: {self.measurement.length} s"))

        filter_layout = QtWidgets.QHBoxLayout()

        filter_layout.addWidget(QtWidgets.QLabel("Filter:"))
        filter_field = QtWidgets.QLineEdit()
        filter_field.setPlaceholderText("Filter signals")
        filter_field.editingFinished.connect(
            lambda: self.handle_filter(filter_field.text()))
        filter_layout.addWidget(filter_field)

        self.main_layout.addLayout(filter_layout)

        list_widget = QtWidgets.QListWidget()
        repo = ChannelRepository()

        for channel in self.measurement.channels:
            if repo.is_name_qualified(channel):
                signal_name = repo.get_signal_name(channel)
            else:
                signal_name = channel.name
            item = QtWidgets.QListWidgetItem(signal_name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, channel)
            list_widget.addItem(item)
        list_widget.itemDoubleClicked.connect(self.handle_channel_clicked)
        self.list_widget = list_widget
        self.main_layout.addWidget(list_widget)

        utils.update_layout(self, self.main_layout)

    def init_deleted_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout()

        self.main_layout.addWidget(
            QtWidgets.QLabel("Measurement has been deleted"))
        utils.update_layout(self, self.main_layout)

    def handle_compare(self):
        comparison_tab = CompareTab(self.measurement)
        main_view = MainView.instance
        main_view.open_tab(f"Compare {self.measurement.name}", comparison_tab)

    def handle_channel_clicked(self, item: QtWidgets.QListWidgetItem):
        channel = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self.channel_window = ChannelPopup(channel)
        self.channel_window.show()

    def handle_filter(self, filter_text: str):
        if filter_text == "":
            for i in range(self.list_widget.count()):
                self.list_widget.item(i).setHidden(False)
            return
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if filter_text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def handle_rename(self):
        text, ok = QtWidgets.QInputDialog.getText(
            self, "Rename Measurement", "New Name:", text=self.measurement.name)
        if ok:
            self.measurement.name = text
            self.registry.save_measurement(self.measurement)
            self.title.setText(f"Measurement: {self.measurement.name}")

    def create_mapping(self):
        self.mapping_window = ChannelAssignmentWindow(self.measurement)
        self.mapping_window.show()

    def delete_measurement(self):
        reply = QtWidgets.QMessageBox.question(
            self, "Delete Measurement", "Are you sure you want to delete this measurement?", QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.registry.delete(self.measurement.id)
            self.init_deleted_ui()

    def add_channel(self):

        self.new_channel_window = NewChannelWindow(self.measurement)

        def add_channel():
            channel = self.measurement.channels[-1]
            item = QtWidgets.QListWidgetItem(channel.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, channel)
            self.list_widget.addItem(item)

        self.new_channel_window.channelAdded.connect(add_channel)
        self.new_channel_window.show()
