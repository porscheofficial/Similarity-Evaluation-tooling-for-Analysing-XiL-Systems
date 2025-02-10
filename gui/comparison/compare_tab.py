from PySide6 import QtCore, QtWidgets, QtGui

from comparison.comparison import Comparison
from gui.comparison.compare_view import CompareView
from gui.comparison.multi_comparison_view import MultiComparisonView
from gui.comparison.prepare_comparison_view import PrepareComparisonView
from gui.comparison.select_other_view import SelectOtherView
from measurement.measurement import Measurement


class CompareTab(QtWidgets.QWidget):
    comparison: Comparison | None = None

    def __init__(self, ref_measurement: Measurement) -> None:
        super().__init__()
        self.reference_measurement = ref_measurement
        self.state = "select_other"
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        stacked_layout = QtWidgets.QStackedLayout()

        select_other_view = SelectOtherView(self.reference_measurement)
        select_other_view.measurement_selected.connect(
            self.handle_measurement_opened)
        stacked_layout.addWidget(select_other_view)
        self.prepare_comparison_view = PrepareComparisonView()
        self.prepare_comparison_view.StartSingleComparison.connect(
            self.start_single_comparison)
        self.prepare_comparison_view.StartMultipleComparison.connect(
            self.start_multiple_comparison)
        stacked_layout.addWidget(self.prepare_comparison_view)
        self.compare_view = CompareView()
        stacked_layout.addWidget(self.compare_view)

        menu_layout = QtWidgets.QHBoxLayout()
        self.back_button = QtWidgets.QPushButton("Back")
        self.back_button.setDisabled(True)
        self.back_button.clicked.connect(self.handle_back)
        menu_layout.addWidget(self.back_button)
        menu_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        layout.addLayout(menu_layout)
        layout.addLayout(stacked_layout)
        self.stacked_layout = stacked_layout
        self.setLayout(layout)

    def handle_back(self):
        index = self.stacked_layout.currentIndex()
        if index > 0:
            self.stacked_layout.setCurrentIndex(index - 1)

        if index == 1:
            self.back_button.setDisabled(True)

    def set_state(self, state):
        self.state = state
        if state == "prepare_comparison":
            self.prepare_comparison_view.set_comparison(self.comparison)
            self.back_button.setDisabled(False)
            self.stacked_layout.setCurrentIndex(1)
        elif state == "select_other":
            self.back_button.setDisabled(True)
            self.stacked_layout.setCurrentIndex(0)
        elif state == "compare":
            self.compare_view.start_comparison(self.comparison)
            self.stacked_layout.setCurrentIndex(2)
            self.back_button.setDisabled(False)

    def handle_measurement_opened(self, measurement: Measurement):
        self.measurement2 = measurement
        comparison = Comparison(
            self.reference_measurement, self.measurement2)
        self.prepare_comparison_view.set_comparison(comparison)
        self.back_button.setDisabled(False)
        self.stacked_layout.setCurrentIndex(1)

    def start_single_comparison(self, comparison: Comparison):
        self.compare_view.start_comparison(comparison)
        self.stacked_layout.insertWidget(2, self.compare_view)
        self.stacked_layout.setCurrentIndex(2)
        self.back_button.setDisabled(False)

    def start_multiple_comparison(self, comparisons: list[Comparison]):
        self.multi_comparison_view = MultiComparisonView(comparisons)
        self.stacked_layout.insertWidget(2, self.multi_comparison_view)
        self.stacked_layout.setCurrentIndex(2)
        self.back_button.setDisabled(False)
