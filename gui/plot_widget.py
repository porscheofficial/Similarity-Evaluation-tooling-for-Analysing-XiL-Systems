import numpy as np
import PySide6.QtWidgets as w
from PySide6.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from logging import getLogger
import matplotlib
import seaborn as sns

from comparison.metrics import MetricResult
from measurement.channel.channel_data import ChannelData
matplotlib.use('Qt5Agg')


class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=6, height=8, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)


class PlotWidget(w.QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.canvas = MplCanvas()
        self.canvas.ax.set_title("Channel Data")
        self.canvas.ax.set_xlabel("Time (s)")
        self.canvas.ax.set_ylabel("Value")
        toolbar = NavigationToolbar(self.canvas, self)
        layout = w.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def plot_channel_data(self, data: ChannelData, color: int = 0):
        color = sns.color_palette('colorblind')[color]
        sns.lineplot({"Time": data.timestamps(), "Value": data.datapoints()}, x="Time", y="Value",
                     ax=self.canvas.ax, color=color)
        self.canvas.draw_idle()

    def plot_vertical_line(self, x: float, color: int = 0, linestyle: str = '-'):
        color = sns.color_palette('colorblind')[color]
        line = self.canvas.ax.axvline(x, color=color, linestyle=linestyle)
        self.canvas.draw_idle()
        return line

    def clear_plot(self):
        self.canvas.ax.clear()
        self.canvas.draw_idle()
