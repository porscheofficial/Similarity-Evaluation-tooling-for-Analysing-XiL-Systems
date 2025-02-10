import logging
import uuid
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import QMetaType
import matplotlib.pyplot as plt

from comparison.comparison_result import ComparisonResult
from gui.comparison.result_tab import ResultTab
from gui.measurement.import_window import ImportWindow
from measurement.measurement import Measurement
from measurement.measurement_import import MeasurementImportInfo
from measurement.measurement_registry import MeasurementRegistry
from gui.files_view import FilesView
from gui.main_view import MainView
from gui.measurement.measurement_tab import MeasurementTab


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle("Analysis Tool")

        self.main_widget = MainView()
        self.menu_bar = MenuBar()
        self.menu_bar.startImport.connect(self.load_measurement)
        self.setMenuBar(self.menu_bar)

        self.main_layout = QtWidgets.QHBoxLayout()
        files_view = FilesView()
        files_view.measurementClicked.connect(self.select_measurement)
        files_view.comparisonClicked.connect(self.open_comparison)
        self.main_layout.addWidget(files_view)
        self.main_layout.addWidget(self.main_widget)

        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

    def load_measurement(self, measurement: MeasurementImportInfo):
        self.logger.debug(f"Loading measurement {measurement}")
        MeasurementRegistry().import_file(measurement)

    def select_measurement(self, measurement: Measurement):
        self.logger.debug(f"Selecting measurement {measurement.name}")
        measurement_display = MeasurementTab(measurement)
        self.main_widget.open_tab(measurement.name, measurement_display)

    def open_comparison(self, comparison: ComparisonResult):
        comparison_result_tab = ResultTab(comparison)
        self.main_widget.open_tab(comparison.name, comparison_result_tab)


class MenuBar(QtWidgets.QMenuBar):
    startImport = QtCore.Signal(MeasurementImportInfo)

    def __init__(self):
        super().__init__()

        file_menu = self.addMenu("File")
        open_action = file_menu.addAction("Import")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction("New", self.new_file)

        comparisons_menu = self.addMenu("Comparisons")

    def open_file(self):
        file_dialog = QtWidgets.QFileDialog()
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        file_dialog.setNameFilter("MDF files (*.mf4)")
        file_dialog.setViewMode(QtWidgets.QFileDialog.Detail)

        if file_dialog.exec():
            filenames = file_dialog.selectedFiles()
            if len(filenames) == 1:
                filename = filenames[0]
                self.import_window = ImportWindow(filename)
                self.import_window.startImport.connect(self.handle_import)
                self.import_window.show()

    def handle_import(self, options: MeasurementImportInfo):
        self.import_window.close()
        self.import_window.deleteLater()
        self.startImport.emit(options)

    def new_file(self):
        name, ok = QtWidgets.QInputDialog.getText(
            self, "New Measurement", "Measurement Name:")
        if ok:
            registry = MeasurementRegistry()

            measurement = Measurement(str(uuid.uuid4()), name, 10, 500, [])
            MeasurementRegistry().add_measurement(measurement)


def start():
    app = QtWidgets.QApplication([])

    window = MainWindow()
    window.resize(800, 500)
    window.show()

    QMetaType(MeasurementImportInfo).registerType()

    app.exec()
