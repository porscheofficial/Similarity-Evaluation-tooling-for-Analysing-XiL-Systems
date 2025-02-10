import logging
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import Signal

from comparison.comparison import Comparison
from comparison.comparison_executor import ComparisonExecutor
from comparison.comparison_repository import ComparisonRepository
from comparison.comparison_result import ComparisonResult
from comparison.sync_block import SyncBlock
from comparison.sync_processor import SyncProcessor
from gui.comparison.channel_assignment_tile import ChannelAssignmentTile
from gui.comparison.channel_prepare_window import ChannelPrepareWindow
from gui.select_multiple_dialog import SelectMultipleDialog
from gui.utils import update_layout
from comparison.metrics.metric_registry import MetricRegistry
from measurement.channel.channel_repository import ChannelRepository


class PrepareComparisonView(QtWidgets.QWidget):
    StartSingleComparison = Signal(Comparison)
    StartMultipleComparison = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.comparison = None
        self.channel_window = None
        self.metric_registry = MetricRegistry()
        self.logger = logging.getLogger(__name__)
        self.setup_ui()

    def set_comparison(self, comparison: Comparison):
        self.logger.info(
            f"Setting comparison: {comparison.ref_measurement.name} vs {comparison.eval_measurement.name}")
        self.comparison = comparison
        self.setup_ui()

    def setup_ui(self):

        if self.comparison is None:
            layout = QtWidgets.QVBoxLayout()
            layout.addWidget(QtWidgets.QLabel("No comparison selected"))
            update_layout(self, layout)
            return

        layout = QtWidgets.QVBoxLayout()

        menu_layout = QtWidgets.QHBoxLayout()

        combo_box = QtWidgets.QComboBox()
        combo_box.addItem("Select Metric")
        for metric in self.metric_registry.metrics:
            combo_box.addItem(metric)

        combo_box.currentTextChanged.connect(self.handle_metric_selected)
        menu_layout.addWidget(combo_box)

        sample_rate = self.comparison.sample_rate

        menu_layout.addWidget(QtWidgets.QLabel(
            f"Sampling Rate: {sample_rate} Hz"))

        start_button = QtWidgets.QPushButton("Start Comparison")
        start_button.clicked.connect(self.handle_start_comparison)
        menu_layout.addWidget(start_button)

        start_multiple_button = QtWidgets.QPushButton("Start Multiple")
        start_multiple_button.clicked.connect(self.handle_start_multiple)
        menu_layout.addWidget(start_multiple_button)

        layout.addLayout(menu_layout)

        list_widget = QtWidgets.QListWidget()
        list_widget.itemDoubleClicked.connect(self.handle_channel_selected)

        if self.comparison is not None:
            self.logger.info("Comparison is present, setting up channel tiles")
            repo = ChannelRepository()
            for channel1 in self.comparison.ref_measurement.channels:
                channel2_name = self.comparison.get_assigned_channel(
                    channel1.name)

                if channel2_name is None:
                    continue
                signal_name = repo.get_signal_name(channel1)
                item = QtWidgets.QListWidgetItem()
                item.setText(f"{signal_name}")
                item.setData(QtCore.Qt.ItemDataRole.UserRole, channel1.name)

                list_widget.addItem(item)
        else:
            layout.addWidget(QtWidgets.QLabel("No comparison selected"))

        layout.addWidget(list_widget)
        update_layout(self, layout)

    def handle_metric_selected(self, metric_name):
        if metric_name == "Select Metric":
            return
        metric = self.metric_registry.get_metric(metric_name)
        self.comparison.set_metric(metric)

    def handle_start_comparison(self):

        if self.comparison is None:
            self.logger.warning("No comparison selected")
            return

        if len(self.comparison.sync_blocks) == 0:
            self.logger.info("Sync end is 0, setting to end of measurement")
            processor = SyncProcessor()
            ref_sync_end, eval_sync_end = processor.find_longest_end_sync_time(0, 0,
                                                                               self.comparison)

            self.comparison.add_sync_block(
                SyncBlock(0, ref_sync_end, 0, eval_sync_end))
            self.logger.info(
                f"Sync end set to {ref_sync_end} and {eval_sync_end}")

        if self.comparison.metric is None:
            self.logger.info("No metric selected")
            box = QtWidgets.QMessageBox.warning(
                self, "No metric selected", "Please select a metric")
            return
        self.StartSingleComparison.emit(self.comparison)

    def handle_channel_selected(self, item: QtWidgets.QListWidgetItem):
        ref_channel_name = item.data(QtCore.Qt.ItemDataRole.UserRole)
        eval_channel_name = self.comparison.get_assigned_channel(
            ref_channel_name)
        if eval_channel_name is None:
            return
        ref_channel = self.comparison.ref_measurement.get_channel_by_name(
            ref_channel_name)
        eval_channel = self.comparison.eval_measurement.get_channel_by_name(
            eval_channel_name)

        channel_window = ChannelPrepareWindow(
            ref_channel, eval_channel, self.comparison)
        channel_window.show()

        if self.channel_window is not None:
            self.channel_window.close()
            self.channel_window.deleteLater()

        self.channel_window = channel_window

    def handle_start_multiple(self):
        options = list(MetricRegistry().available_metrics())
        dialog = SelectMultipleDialog(options)
        result = dialog.exec()
        if result == QtWidgets.QDialog.Accepted:
            metrics = dialog.getSelection()
            self.logger.info(f"Selected metrics: {metrics}")
            metric_registry = MetricRegistry()
            metrics = [metric_registry.get_metric(
                metric) for metric in metrics]

            if len(self.comparison.sync_blocks) == 0:
                self.logger.info(
                    "No sync blocks found, setting to end of measurement")
                processor = SyncProcessor()
                ref_sync_end, eval_sync_end = processor.find_longest_end_sync_time(0, 0,
                                                                                   self.comparison)

                self.comparison.add_sync_block(
                    SyncBlock(0, ref_sync_end, 0, eval_sync_end))
                self.logger.info(
                    f"Sync end set to {ref_sync_end} and {eval_sync_end}")

            comparisons = [self.comparison.copy() for _ in metrics]
            for comparison, metric in zip(comparisons, metrics):
                comparison.set_metric(metric)

            comparisons = list(comparisons)
            self.logger.info(f"Starting multiple comparisons: {comparisons}")
            self.StartMultipleComparison.emit(comparisons)
