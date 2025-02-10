from logging import getLogger
import PySide6.QtWidgets as w
from PySide6.QtCore import Signal, Qt

from comparison.comparison import Comparison
from comparison.comparison_executor import MultiComparisonExecutor
from comparison.comparison_result import ComparisonResult
from gui import utils
from gui.comparison.compare_view import CompareView


class MultiComparisonView(w.QWidget):
    def __init__(self, comparisons: list[Comparison]) -> None:
        super().__init__()
        self.logger = getLogger(__name__)
        self.comparisons = comparisons
        self.logger.info(
            f"Opened ComparisonView with {len(comparisons)} comparisons")
        self.setup_loading_ui()
        self.execute_comparisons()

    def execute_comparisons(self):
        self.comparison_results = []
        self.comparison_index = 0
        self.comparison_exec = MultiComparisonExecutor(self.comparisons)
        self.comparison_exec.doneAll.connect(self.handle_comparisons_done)
        self.comparison_exec.start()

    def setup_loading_ui(self):
        layout = w.QVBoxLayout()
        layout.addWidget(w.QLabel("Loading comparisons..."))
        progress = w.QProgressBar()
        progress.setRange(0, 0)
        layout.addWidget(progress)

        utils.update_layout(self, layout)

    def setup_done_ui(self):
        layout = w.QHBoxLayout()

        self.comparison_list_widget = w.QListWidget()
        self.comparison_list_widget.setFixedWidth(300)
        self.comparison_list_widget.itemDoubleClicked.connect(
            self.handle_comparison_opened)

        layout.addWidget(self.comparison_list_widget)

        self.comparison_view = CompareView()
        layout.addWidget(self.comparison_view)

        utils.update_layout(self, layout)

    def handle_comparison_opened(self, item: w.QListWidgetItem):
        comparison_result: ComparisonResult = item.data(
            Qt.ItemDataRole.UserRole)
        self.comparison_view.set_result(comparison_result)

    def handle_comparisons_done(self, results: list[ComparisonResult]):
        self.comparison_results = results
        self.setup_done_ui()

        for result in results:
            item = w.QListWidgetItem(
                f"{result.name}")
            item.setData(Qt.ItemDataRole.UserRole, result)
            self.comparison_list_widget.addItem(item)
