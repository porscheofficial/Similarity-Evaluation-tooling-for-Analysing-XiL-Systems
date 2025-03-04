from PySide6 import QtCore, QtWidgets, QtGui

from comparison.comparison import Comparison


class ComparePreparationDisplay(QtWidgets.QWidget):
    def __init__(self, comparison: Comparison):
        super().__init__()
        self.comparison = comparison

        self.layout = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel(
            f"Compare {self.comparison.file1.filename} with {self.comparison.file2.filename}")
        title.setStyleSheet("font-size: 20px")
        self.layout.addWidget(title)

        scroll_area = QtWidgets.QScrollArea()

        self.channel_layout = QtWidgets.QVBoxLayout()
        for channel in self.comparison.file1.channels:
            channel_assignment = ChannelAssignmentDisplay(
                channel, self.comparison, None)
            self.channel_layout.addWidget(channel_assignment)

        channels_widget = QtWidgets.QWidget()
        channels_widget.setLayout(self.channel_layout)
        scroll_area.setWidget(channels_widget)

        self.layout.addWidget(scroll_area)

        self.setLayout(self.layout)


class ChannelAssignmentDisplay(QtWidgets.QWidget):
    def __init__(self, channel1: str, comparison: Comparison, update_callback):
        super().__init__()
        self.channel1 = channel1
        self.comparison = comparison

        self.setWindowState(QtCore.Qt.WindowFullScreen)
        self.setMinimumWidth(1000)

        self.layout = QtWidgets.QHBoxLayout()
        channel1_short = channel1[-50:]
        self.channel1_label = QtWidgets.QLabel(channel1_short)
        self.channel1_label.setToolTip(channel1)

        if comparison.get_assigned_channel(channel1) is None:
            self.channel2_label = QtWidgets.QLabel("Not Assigned")
        else:
            channel2 = comparison.get_assigned_channel(channel1)
            channel2_short = channel2[-50:]
            self.channel2_label = QtWidgets.QLabel(channel2_short)
            self.channel2_label.setToolTip(channel2)

        self.layout.addWidget(self.channel1_label)
        self.layout.addWidget(QtWidgets.QLabel("<->"))
        self.layout.addWidget(self.channel2_label)
        self.layout.addStretch()

        assign_button = QtWidgets.QPushButton("Assign")
        assign_button.setFixedSize(100, 30)

        toggle_input_text = "Remove Input" if channel1 in comparison.input_channels else "Set Input"
        toggle_input_button = QtWidgets.QPushButton(toggle_input_text)
        toggle_input_button.setFixedSize(100, 30)

        delete_button = QtWidgets.QPushButton("Remove from Comparison")
        delete_button.setFixedSize(150, 30)
        delete_button.setStyleSheet("background-color: red; color: white")

        self.layout.addWidget(assign_button)
        self.layout.addWidget(toggle_input_button)
        self.layout.addWidget(delete_button)

        self.setLayout(self.layout)
