import PySide6.QtWidgets as w
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QDoubleValidator
from gui.plot_widget import PlotWidget
from measurement.channel.channel import Channel
from measurement.channel.channel_data_repository import ChannelDataRepository
from measurement.channel.channel_generator import ChannelGenerator
from measurement.channel.channel_repository import ChannelRepository
from measurement.measurement import Measurement
from measurement.measurement_registry import MeasurementRegistry


class NewChannelWindow(w.QWidget):
    channelAdded = Signal()

    def __init__(self, measurement: Measurement) -> None:
        super().__init__()
        self.measurement = measurement
        self.channel_data = None

        # Set window title
        self.setWindowTitle("New Channel")

        # Create widgets
        self.channel_type_label = w.QLabel("Select Channel Type:")
        self.channel_type_combo = w.QComboBox()
        self.channel_type_combo.addItems(
            ["Select Type", "Sinus Channel", "Gaussian Curve Channel", "Square Wave Channel", "Block Channel", "Sawtooth Wave Channel"])

        self.channel_name_label = w.QLabel("Channel Name:")
        self.channel_name_edit = w.QLineEdit()

        self.scale_label = w.QLabel("Scale (y):")
        self.scale_edit = w.QLineEdit()
        self.scale_edit.setText("1.0")

        self.offset_label = w.QLabel("Offset (s):")
        self.offset_edit = w.QLineEdit()
        self.offset_edit.setText("0.0")

        self.stretch_label = w.QLabel("Stretch:")
        self.stretch_edit = w.QLineEdit()
        self.stretch_edit.setText("1.0")

        self.add_button = w.QPushButton("Add Channel")
        self.cancel_button = w.QPushButton("Cancel")

        # Create Preview Plot
        self.plot = PlotWidget()

        # Set layout
        layout = w.QVBoxLayout()

        form_layout = w.QFormLayout()
        form_layout.addRow(self.channel_type_label, self.channel_type_combo)
        form_layout.addRow(self.channel_name_label, self.channel_name_edit)
        form_layout.addRow(self.scale_label, self.scale_edit)
        form_layout.addRow(self.offset_label, self.offset_edit)
        form_layout.addRow(self.stretch_label, self.stretch_edit)

        button_layout = w.QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.cancel_button)

        layout.addWidget(self.plot)
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connect signals and slots
        self.add_button.clicked.connect(self.add_channel)
        self.cancel_button.clicked.connect(self.close)

        self.channel_type_combo.currentTextChanged.connect(self.update_preview)
        self.scale_edit.editingFinished.connect(self.update_preview)
        self.offset_edit.editingFinished.connect(self.update_preview)
        self.stretch_edit.editingFinished.connect(self.update_preview)
        self.channel_name_edit.editingFinished.connect(self.update_preview)

    def add_channel(self):
        if self.channel_data is None:
            w.QMessageBox.warning(self, "Error", "No channel data generated.")
            return
        if self.channel_data.name == "":
            w.QMessageBox.warning(
                self, "Error", "Channel name cannot be empty.")
            return
        repo = ChannelRepository()
        channel = Channel(self.channel_data.id,
                          self.channel_data.name, [self.channel_data.name], {})
        repo.store(channel)
        self.measurement.add_channel(channel)
        repo = ChannelDataRepository()
        repo.store(self.channel_data)
        repo = MeasurementRegistry()
        repo.save_measurement(self.measurement)
        self.channelAdded.emit()
        w.QMessageBox.information(
            self, "Success", "Channel added successfully.")

        self.close()

    def update_preview(self):
        channel_type = self.channel_type_combo.currentText()
        self.plot.clear_plot()
        self.channel_data = None
        generator = ChannelGenerator()
        if channel_type == "Select Type":
            return
        try:
            scale = float(self.scale_edit.text())
            offset = float(self.offset_edit.text())
            stretch = float(self.stretch_edit.text())
            stretch = 1 / stretch
        except ValueError:
            return
        if channel_type == "Sinus Channel":
            self.channel_data = generator.generate_sinus(
                scale, offset, stretch,
                self.channel_name_edit.text(),
                self.measurement
            )
        elif channel_type == "Gaussian Curve Channel":
            self.channel_data = generator.generate_gaussian_curve(
                scale, offset, stretch,
                self.channel_name_edit.text(),
                self.measurement
            )
        elif channel_type == "Square Wave Channel":
            self.channel_data = generator.generate_square_wave(
                scale, offset, stretch,
                self.channel_name_edit.text(),
                self.measurement
            )
        elif channel_type == "Block Channel":
            self.channel_data = generator.generate_block(
                scale, offset, stretch,
                self.channel_name_edit.text(),
                self.measurement
            )
        elif channel_type == "Sawtooth Wave Channel":
            self.channel_data = generator.generate_sawtooth_wave(
                scale, offset, stretch,
                self.channel_name_edit.text(),
                self.measurement
            )

        self.plot.plot_channel_data(self.channel_data)
