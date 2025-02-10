import logging
from PySide6 import QtCore, QtWidgets, QtGui
from comparison.comparison_repository import ComparisonRepository
from comparison.comparison_result import ComparisonResult
from measurement.measurement import Measurement
from measurement.measurement_registry import MeasurementRegistry


class FilesView(QtWidgets.QWidget):
    measurementClicked = QtCore.Signal(Measurement)
    comparisonClicked = QtCore.Signal(ComparisonResult)

    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.measurement_list_widget = QtWidgets.QListWidget()
        self.comparison_list_widget = QtWidgets.QListWidget()
        self.setFixedWidth(400)

        self.measurement_registry = MeasurementRegistry()
        self.measurement_registry.measurements_updated.connect(
            self.handle_import)
        self.comparison_repo = ComparisonRepository()
        self.comparison_repo.loadingDone.connect(self.comparisonClicked.emit)
        self.comparison_repo.listUpdated.connect(
            self.handle_comparisons_updated)

        measurements = self.measurement_registry.measurements
        measurements = sorted(measurements, key=lambda x: x.name)

        for measurement in measurements:
            item = QtWidgets.QListWidgetItem(measurement.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, measurement)
            self.measurement_list_widget.addItem(item)

        for comparison in sorted(self.comparison_repo.comparison_names):
            self.comparison_list_widget.addItem(comparison)

        self.comparison_list_widget.itemDoubleClicked.connect(
            self.handle_comparison_opened)

        self.measurement_list_widget.itemDoubleClicked.connect(
            self.handle_measurement_opened)

        layout = QtWidgets.QVBoxLayout()

        tab_widget = QtWidgets.QTabWidget()
        tab_widget.setTabsClosable(False)
        tab_widget.addTab(self.measurement_list_widget, "Measurements")
        tab_widget.addTab(self.comparison_list_widget, "Comparisons")

        layout.addWidget(tab_widget)
        self.setLayout(layout)

    def handle_import(self):
        self.logger.info("Handling file import, refreshing list")
        self.measurement_list_widget.clear()
        measurements = self.measurement_registry.measurements
        measurements = sorted(measurements, key=lambda x: x.name)
        for measurement in measurements:
            item = QtWidgets.QListWidgetItem(measurement.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, measurement)
            self.measurement_list_widget.addItem(item)

    def handle_comparisons_updated(self):
        self.logger.info("Handling comparisons updated, refreshing list")
        self.comparison_list_widget.clear()
        for comparison in sorted(self.comparison_repo.comparison_names):
            self.comparison_list_widget.addItem(comparison)

    def handle_measurement_opened(self, item: QtWidgets.QListWidgetItem):
        self.logger.info(f"Opening measurement {item.text()}")
        measurement: Measurement = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self.measurementClicked.emit(measurement)

    def handle_comparison_opened(self, item):
        self.logger.info(f"Opening comparison {item.text()}")
        comparison = item.text()
        self.comparison_repo.load_comparison(comparison)
