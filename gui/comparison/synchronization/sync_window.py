from comparison.comparison import Comparison
import matplotlib.pyplot as plt
import PySide6.QtWidgets as w
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from logging import getLogger
import matplotlib

from comparison.sync_processor import SyncProcessor
from measurement.channel.channel_data_repository import ChannelDataRepository
matplotlib.use('Qt5Agg')


class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)


class SyncWindow(w.QWidget):
    def __init__(self, comparison: Comparison, ref_channel_name: str, eval_channel_name: str):
        super().__init__()
        self.comparison = comparison

        repo = ChannelDataRepository()
        ref_channel = self.comparison.ref_measurement.get_channel_by_name(
            ref_channel_name)
        self.ref_channel = repo.load_from_channel(ref_channel)
        eval_channel = self.comparison.eval_measurement.get_channel_by_name(
            eval_channel_name)
        self.eval_channel = repo.load_from_channel(eval_channel)
        self.logger = getLogger(__name__)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Sync Window")
        self.main_layout = w.QVBoxLayout()
        self.setLayout(self.main_layout)

        self.cv = MplCanvas()

        self.draw_data()
        self.main_layout.addWidget(self.cv)

        self.main_layout.addWidget(w.QLabel("Synchronize when value reaches:"))
        self.sync_value_input = w.QLineEdit()
        self.main_layout.addWidget(self.sync_value_input)

        self.sync_button = w.QPushButton("Synchronize")
        self.sync_button.clicked.connect(self.handle_sync)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.sync_button)

    def draw_data(self):
        ref_channel = self.ref_channel
        x1_data = ref_channel.timestamps()
        y1_data = ref_channel.datapoints()
        self.cv.ax.plot(x1_data, y1_data)
        eval_channel = self.eval_channel
        x2_data = eval_channel.timestamps()
        y2_data = eval_channel.datapoints()
        self.cv.ax.plot(x2_data, y2_data)

    def handle_sync(self):
        sync_value = 0
        try:
            sync_value = float(self.sync_value_input.text())
        except ValueError:
            self.logger.error("Sync value must be a number")
            w.QMessageBox.warning(self, "Sync Value Error",
                                  "Sync value must be a number", w.QMessageBox.Ok)
            return
        self.logger.info(f"Syncing at value {sync_value}")

        processor = SyncProcessor()

        processor.sync(self.comparison, self.ref_channel,
                       self.eval_channel, sync_value)

        self.logger.info(
            f"Sync start times are \t{self.comparison.ref_sync_start:.5f}, {self.comparison.eval_sync_start:.5f}")
        self.logger.info(
            f"Sync end times are \t{self.comparison.ref_sync_end:.5f}, {self.comparison.eval_sync_end:.5f}")

        self.cv.ax.clear()
        self.draw_data()

        # Draw vertical lines at sync times
        self.cv.ax.axvline(self.comparison.ref_sync_start,
                           color='b', linestyle='--')
        self.cv.ax.axvline(self.comparison.eval_sync_start,
                           color='r', linestyle='--')
        self.cv.draw_idle()
