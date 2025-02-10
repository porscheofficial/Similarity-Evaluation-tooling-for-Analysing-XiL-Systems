import logging
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGridLayout, QPushButton, QScrollArea, QSizePolicy
import PySide6.QtWidgets as widgets

from comparison.comparison import Comparison
from comparison.comparison_executor import ComparisonExecutor
from comparison.comparison_repository import ComparisonRepository
from comparison.comparison_result import ComparisonResult
from gui.comparison.plot_metric_result import PlotMetricResult
import gui.utils as utils

import matplotlib.pyplot as plt


class CompareView(QWidget):
    comparison: Comparison | None = None

    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.comparison_result = None
        self.executor = None
        self.init_no_ui()

    def init_no_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(QLabel("No comparison selected"))
        utils.update_layout(self, self.main_layout)

    def init_done_ui(self):

        if self.comparison_result is None:
            self.logger.warning("No comparison set")
            return

        self.main_layout = QVBoxLayout()

        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setSizeConstraint(
            QVBoxLayout.SizeConstraint.SetMinAndMaxSize)

        list_widget = widgets.QTableWidget()
        list_widget.setColumnCount(2)
        list_widget.setHorizontalHeaderLabels(["Signal", "Mean"])
        list_widget.setColumnWidth(0, 300)

        for i, (ref_ch, eval_ch, result) in enumerate(self.comparison_result.channel_results):
            mean = result.result.mean()
            tile = widgets.QTableWidgetItem()
            mean_tile = widgets.QTableWidgetItem()
            tile.setText(f"{ref_ch.name}")
            tile.setData(Qt.ItemDataRole.UserRole, i)
            tile.setSizeHint(QSize(300, 30))
            mean_tile.setText(f"{mean:.4f}")
            mean_tile.setData(Qt.ItemDataRole.UserRole, i)

            if mean < 0.4:
                tile.setBackground(Qt.GlobalColor.red)
                mean_tile.setBackground(Qt.GlobalColor.red)
            elif mean < 0.6:
                tile.setBackground(Qt.GlobalColor.darkYellow)
                mean_tile.setBackground(Qt.GlobalColor.darkYellow)
            elif mean < 0.8:
                tile.setBackground(Qt.GlobalColor.yellow)
                mean_tile.setBackground(Qt.GlobalColor.yellow)
            elif mean < 0.9:
                tile.setBackground(Qt.GlobalColor.darkGreen)
                mean_tile.setBackground(Qt.GlobalColor.darkGreen)
            else:
                tile.setBackground(Qt.GlobalColor.green)
                mean_tile.setBackground(Qt.GlobalColor.green)

            list_widget.insertRow(i)
            list_widget.setItem(i, 0, tile)
            list_widget.setItem(i, 1, mean_tile)

        list_widget.itemDoubleClicked.connect(self.handle_channel_selected)
        self.main_layout.addWidget(list_widget)

        self.summary_layout = QHBoxLayout()

        mean = self.comparison_result.result_average

        self.total_label = QLabel(f"Total: {mean:.2f}")
        self.plot_button = QPushButton("Plot")
        self.plot_button.clicked.connect(self.handle_plot_button)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.handle_save_button)

        self.summary_layout.addWidget(self.total_label)
        self.summary_layout.addWidget(self.plot_button)
        self.summary_layout.addWidget(self.save_button)

        self.main_layout.addLayout(self.summary_layout)

        utils.update_layout(self, self.main_layout)

    def init_loading_ui(self):
        self.main_layout = QVBoxLayout()
        loading_indicator = widgets.QProgressBar()
        loading_indicator.setRange(0, 0)
        loading_indicator.setFormat("Loading...")
        self.main_layout.addWidget(loading_indicator)
        utils.update_layout(self, self.main_layout)

    def start_comparison(self, comparison: Comparison):
        if self.executor is not None:
            self.executor.quit()
            self.executor.wait()

        self.executor = ComparisonExecutor(comparison)
        self.executor.done.connect(self.handle_comparison_finished)
        self.executor.start()

        self.init_loading_ui()

    def set_result(self, comparison_result: ComparisonResult):
        self.comparison_result = comparison_result
        self.init_done_ui()

    def handle_comparison_finished(self, comparison_result: ComparisonResult):
        self.logger.info("Comparison finished")
        self.comparison_result = comparison_result
        self.init_done_ui()

    def handle_channel_selected(self, item: widgets.QListWidgetItem):
        index = item.data(Qt.ItemDataRole.UserRole)
        ref_ch, eval_ch, result = self.comparison_result.channel_results[index]
        self.logger.info(
            f"Channel selected: {ref_ch.name} vs {eval_ch.name}")
        self.channel_plot_window = PlotMetricResult(result)
        self.channel_plot_window.show()

    def handle_plot_button(self):
        x_data = self.comparison_result.result.timestamps
        y_data = self.comparison_result.result.values

        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        ax.plot(x_data, y_data)
        ax.set_xlabel("Time")
        ax.set_ylabel("Average Metric Value")
        ax.set_title(f"Total Comparison")

        plt.show()

    def handle_save_button(self):
        self.save_button.setEnabled(False)
        repo = ComparisonRepository()

        dialog = widgets.QInputDialog()
        dialog.setWindowTitle("Save Comparison")
        dialog.setLabelText("Enter a name for the comparison:")
        dialog.setTextValue(self.comparison_result.name)
        if not dialog.exec():
            self.save_button.setEnabled(True)
            return

        self.comparison_result.name = dialog.textValue()

        if self.comparison_result.name in repo.comparison_names:
            self.logger.warning(
                f"Comparison with name {self.comparison_result.name} already exists.")

        self.logger.info("Saving comparison")

        ComparisonRepository().save_comparison(self.comparison_result)
