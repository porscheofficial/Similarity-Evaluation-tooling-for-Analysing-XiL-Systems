from logging import getLogger
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGridLayout, QPushButton, QScrollArea, QSizePolicy, QCheckBox, QFileDialog, QLineEdit, QFrame

from PySide6.QtCore import Signal

from gui.measurement.channel_assignment_window import ChannelAssignmentWindow
from measurement.measurement_import import MeasurementImportInfo
import gui.utils as utils

import os

import pandas as pd


class ImportWindow(QWidget):
    startImport = Signal(MeasurementImportInfo)

    def __init__(self, filename: str) -> None:
        super().__init__()
        self.logger = getLogger(__name__)
        self.filename = filename
        self.name_mapping_filename = None
        self.options = MeasurementImportInfo(filename, False, False, {}, 100)
        self.sample_rate_invalid = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Import Measurement: {self.filename}"))

        remove_constant_channels = QCheckBox("Remove Constant Null Signals")
        remove_constant_channels.setChecked(self.options.remove_constant_channels)
        remove_constant_channels.clicked.connect(
            lambda: self.handle_constant_channels(remove_constant_channels.isChecked()))
        layout.addWidget(remove_constant_channels)
        merge_duplicate_channels = QCheckBox("Merge Repeated Signals")
        merge_duplicate_channels.setChecked(self.options.merge_signals)

        def handle_merge_duplicate_channels():
            self.options.merge_signals = merge_duplicate_channels.isChecked()
            self.logger.info(
                f"Merge duplicate channels: {self.options.merge_signals}")
        merge_duplicate_channels.clicked.connect(
            handle_merge_duplicate_channels)
        layout.addWidget(merge_duplicate_channels)

        name_mapping_layout = QHBoxLayout()
        if self.name_mapping_filename is None:
            name_mapping_layout.addWidget(
                QLabel("No name mapping file selected"))
        else:
            name_mapping_layout.addWidget(
                QLabel(f"Name mapping file: {os.path.basename(self.name_mapping_filename)}"))

        name_mapping_layout.addStretch()

        if self.name_mapping_filename is not None:
            button = QPushButton("Clear Name Mapping File")
            button.clicked.connect(self.handle_clear_name_mapping)
            name_mapping_layout.addWidget(button)
        else:
            button = QPushButton("Select Name Mapping File")
            button.clicked.connect(self.handle_select_name_mapping)
            name_mapping_layout.addWidget(button)
        layout.addLayout(name_mapping_layout)

        sample_rate_layout = QHBoxLayout()
        sample_rate_layout.addWidget(QLabel("Sample Rate: "))
        sample_rate_layout.addStretch()
        text_field = QLineEdit()
        text_field.setText(str(self.options.sample_rate))
        text_field.editingFinished.connect(
            lambda: self.handle_sample_rate(text_field.text()))
        sample_rate_layout.addWidget(text_field)
        sample_rate_layout.addWidget(QLabel("Hz"))

        if self.sample_rate_invalid:
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.Box)
            frame.setStyleSheet("background-color: red")
            frame_layout = QVBoxLayout()
            frame_layout.addWidget(QLabel("Invalid sample rate"))
            frame.setLayout(frame_layout)
            layout.addWidget(frame)

        layout.addLayout(sample_rate_layout)

        layout.addStretch()

        import_button = QPushButton("Import")
        import_button.clicked.connect(self.handle_import)

        layout.addWidget(import_button)

        utils.update_layout(self, layout)

    def handle_constant_channels(self, checked: bool):
        self.options.remove_constant_channels = checked
        self.logger.info(
            f"Remove zero channels: {self.options.remove_constant_channels}")

    def handle_clear_name_mapping(self):
        self.name_mapping_filename = None
        self.logger.info("Name mapping file cleared")
        self.setup_ui()

    def handle_select_name_mapping(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("CSV Files (*.csv)")
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)

        if dialog.exec():
            filenames = dialog.selectedFiles()
            if len(filenames) == 1:
                self.name_mapping_filename = filenames[0]
                self.logger.info(
                    f"Selected name mapping file: {self.name_mapping_filename}")
                self.setup_ui()
            else:
                self.logger.error("No file selected")

    def handle_sample_rate(self, text: str):
        try:
            sample_rate = float(text)
            self.options.sample_rate = sample_rate
            self.logger.info(f"Sample rate set to {sample_rate}")
            self.sample_rate_invalid = False
            self.setup_ui()
        except ValueError:
            self.logger.error("Invalid sample rate")
            self.sample_rate_invalid = True
            self.setup_ui()

    def handle_import(self):
        if self.sample_rate_invalid:
            self.logger.error("Sample rate invalid")
            return

        if self.name_mapping_filename is not None:
            self.options.name_mapping = self.read_name_mapping(
                self.name_mapping_filename)

        self.logger.info("Importing measurement")
        self.startImport.emit(self.options)

    def read_name_mapping(self, filename: str):
        self.logger.info(f"Reading name mapping from {filename}")
        data = pd.read_csv(filename)
        mapping = {}
        for index, row in data.iterrows():
            channel = row["Channel"]
            mapped_channel = row["Mapped Channel"]
            mapping[channel] = mapped_channel

        return mapping
