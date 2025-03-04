from logging import getLogger
from PySide6 import QtWidgets, QtCore

from measurement.measurement import Measurement
from measurement.measurement_registry import MeasurementRegistry


class SelectOtherView(QtWidgets.QWidget):
    measurement_selected = QtCore.Signal(Measurement)

    def __init__(self, ref_measurement: Measurement) -> None:
        super().__init__()
        self.ref_measurement = ref_measurement
        self.logger = getLogger(__name__)
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Create a label to display the channel name
        channel_label = QtWidgets.QLabel("Select other measurement")
        channel_label.setStyleSheet("font-size: 20px")
        layout.addWidget(channel_label)

        list_widget = QtWidgets.QListWidget()
        measurements = MeasurementRegistry().measurements
        for measurement in sorted(measurements, key=lambda m: m.name):
            if measurement.sample_rate != self.ref_measurement.sample_rate:
                self.logger.info(
                    f"Skipping {measurement.name} due to different sample rate")
                continue

            list_widget.addItem(measurement.name)

        list_widget.itemDoubleClicked.connect(self.handle_measurement_opened)

        layout.addWidget(list_widget)

        self.setLayout(layout)

    def handle_measurement_opened(self, item):
        measurement = MeasurementRegistry().get_by_name(item.text())
        self.measurement_selected.emit(measurement)
