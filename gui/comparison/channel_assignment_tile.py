from PySide6 import QtCore, QtWidgets, QtGui

from comparison.comparison import Comparison
import matplotlib.pyplot as plt

from gui.comparison.synchronization.sync_window import SyncWindow
from gui.utils import crop_text_end, update_layout, update_ui


class ChannelAssignmentTile(QtWidgets.QFrame):
    sync_popup: QtWidgets.QWidget

    def __init__(self, channel1: str, channel2: str | None, comparison: Comparison) -> None:
        super().__init__()
        self.channel1 = channel1
        self.channel2 = channel2
        self.comparison = comparison
        self.setup_ui()

    def setup_ui(self):
        self.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        layout = QtWidgets.QHBoxLayout(self)

        label1 = QtWidgets.QLabel(crop_text_end(self.channel1, 100))
        label2 = QtWidgets.QLabel(
            (crop_text_end(self.channel2, 100) if self.channel2 is not None else "None"))

        label1.setToolTip(self.channel1)
        if self.channel2 is not None:
            label2.setToolTip(self.channel2)

        label_layout = QtWidgets.QVBoxLayout()
        label_layout.addWidget(label1)
        label_layout.addWidget(label2)

        layout.addLayout(label_layout)
        layout.addWidget(QtWidgets.QLabel("<->"))
        layout.addStretch()

        assign_text = "Assign" if self.channel2 is None else "Assign Other"
        assign_button = QtWidgets.QPushButton(assign_text)
        assign_button.clicked.connect(self.handle_assign)
        layout.addWidget(assign_button)

        if self.channel2 is not None:
            plot_button = QtWidgets.QPushButton("Plot")
            plot_button.clicked.connect(self.handle_plot)
            layout.addWidget(plot_button)
            sync_button = QtWidgets.QPushButton("Sync")
            sync_button.clicked.connect(self.handle_sync)
            layout.addWidget(sync_button)
        self.setLayout(layout)

    def update_ui(self):
        update_ui(self, self.setup_ui)

    def handle_assign(self):
        self.select_popup = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.select_popup)
        layout.addWidget(QtWidgets.QLabel("Select channel to assign"))
        list_widget = QtWidgets.QListWidget()
        measurements = self.comparison.eval_measurement.channels
        for channel in measurements:
            list_widget.addItem(channel.name)
        list_widget.itemDoubleClicked.connect(self.handle_channel_selected)
        layout.addWidget(list_widget)
        self.select_popup.setLayout(layout)
        self.select_popup.show()

    def handle_channel_selected(self, item):
        self.channel2 = item.text()
        self.comparison.assign_channel(self.channel1, self.channel2)
        self.select_popup.close()
        self.update_ui()

    def handle_plot(self):
        channel1 = self.comparison.ref_measurement.get_channel(self.channel1)
        channel2 = self.comparison.eval_measurement.get_channel(self.channel2)
        channel1 = channel1.load_channel()
        channel2 = channel2.load_channel()

        plt.plot(channel1.timestamps(), channel1.datapoints(),
                 drawstyle='steps-post')
        plt.plot(channel2.timestamps(), channel2.datapoints(),
                 drawstyle='steps-post')
        plt.xlabel("Time (s)")
        plt.ylabel("Value")
        plt.legend([self.comparison.ref_measurement.name,
                   self.comparison.eval_measurement.name])
        plt.show()

    def handle_sync(self):
        self.sync_popup = SyncWindow(
            self.comparison, self.channel1, self.channel2)
        self.sync_popup.show()
