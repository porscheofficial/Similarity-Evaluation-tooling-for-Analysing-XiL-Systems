import numpy as np
import PySide6.QtWidgets as w
from PySide6.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from logging import getLogger
import matplotlib

from comparison.metrics import MetricResult
matplotlib.use('Qt5Agg')


class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=6, height=8, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.result_ax = self.fig.add_subplot(211)
        self.channel_ax = self.fig.add_subplot(212, sharex=self.result_ax)
        super(MplCanvas, self).__init__(self.fig)


class PlotMetricResult(w.QWidget):
    def __init__(self, result: MetricResult) -> None:
        super().__init__()
        self.logger = getLogger("MAIN")
        self.result = result

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Plot Metric Result")
        self.main_layout = w.QVBoxLayout()
        self.cv = MplCanvas()
        toolbar = NavigationToolbar(self.cv, self)
        self.main_layout.addWidget(toolbar)
        self.main_layout.addWidget(self.cv)
        self.main_layout.addStretch()
        self.main_layout.addWidget(w.QLabel("Metric Result Metadata"))
        grid = w.QGridLayout()
        self.metric_result_metadata_checkboxes = {}
        for i, (key, _) in enumerate(self.result.result_metadata.items()):
            horizontal_i = i % 2
            vertical_i = i // 2
            check_box = w.QCheckBox()
            check_box.setChecked(False)
            check_box.clicked.connect(self.draw_data)
            self.metric_result_metadata_checkboxes[key] = check_box
            grid.addWidget(w.QLabel(key), vertical_i, horizontal_i * 2)
            grid.addWidget(check_box, vertical_i, horizontal_i * 2 + 1)

        self.main_layout.addLayout(grid)
        self.main_layout.addWidget(w.QLabel("Channel Metadata"))
        grid = w.QGridLayout()
        self.metric_input_metadata_checkboxes = {}
        for i, (key, _) in enumerate(self.result.input_metadata.items()):
            horizontal_i = i % 2
            vertical_i = i // 2
            check_box = w.QCheckBox()
            check_box.setChecked(False)
            check_box.clicked.connect(self.draw_data)
            self.metric_input_metadata_checkboxes[key] = check_box
            grid.addWidget(w.QLabel(key), vertical_i, horizontal_i * 2)
            grid.addWidget(check_box, vertical_i, horizontal_i * 2 + 1)

        self.main_layout.addLayout(grid)

        self.setLayout(self.main_layout)

        self.draw_data()

    def draw_data(self):
        length = len(self.result.result)

        self.cv.result_ax.clear()
        self.cv.channel_ax.clear()

        self.cv.result_ax.plot(self.result.result.timestamps, self.result.result.values,
                               drawstyle='steps-post', label="Metric Result")
        self.cv.result_ax.set_title("Metric Result")
        self.cv.result_ax.set_xlabel("Time")
        self.cv.result_ax.set_ylabel("Value")

        for key, metadata_signal in self.result.result_metadata.items():
            if self.metric_result_metadata_checkboxes[key].isChecked():
                self.cv.result_ax.plot(metadata_signal.timestamps, metadata_signal.values,
                                       drawstyle='steps-post', label=key)

        # self.cv.result_ax.legend()
        self.cv.channel_ax.plot(self.result.reference_input.timestamps, self.result.reference_input.values,
                                drawstyle='steps-post', label="Reference Channel")
        self.cv.channel_ax.plot(self.result.evaluated_input.timestamps, self.result.evaluated_input.values,
                                drawstyle='steps-post', label="Evaluated Channel")
        self.cv.channel_ax.set_title("Channel Data")
        self.cv.channel_ax.set_xlabel("Time")
        self.cv.channel_ax.set_ylabel("Value")

        for key, metadata_signal in self.result.input_metadata.items():
            if self.metric_input_metadata_checkboxes[key].isChecked():
                color = "cyan"
                if "outer_corridor" in key:
                    color = "red"
                elif "inner_corridor" in key:
                    color = "green"
                self.cv.channel_ax.plot(metadata_signal.timestamps, metadata_signal.values,
                                        drawstyle='steps-post', label=key, color=color)

        # self.cv.channel_ax.legend()
        self.cv.draw_idle()
