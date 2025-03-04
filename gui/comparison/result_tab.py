from PySide6 import QtWidgets as w
from PySide6.QtCore import QTimer

from comparison.comparison_result import ComparisonResult
from gui.comparison.compare_view import CompareView


class ResultTab(w.QWidget):

    def __init__(self, result: ComparisonResult):
        super().__init__()

        layout = w.QVBoxLayout()

        compare_view = CompareView()

        QTimer.singleShot(0, lambda: compare_view.set_result(result))

        layout.addWidget(compare_view)

        self.setLayout(layout)
