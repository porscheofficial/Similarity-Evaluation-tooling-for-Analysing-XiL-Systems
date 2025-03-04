import PySide6.QtWidgets as w

from comparison.comparison import Comparison
from comparison.sync_processor import SyncProcessor
from gui.plot_widget import PlotWidget
from measurement.channel.channel import Channel
from measurement.channel.channel_data_repository import ChannelDataRepository

import gui.utils as utils
from measurement.channel.channel_repository import ChannelRepository


class ChannelPrepareWindow(w.QWidget):
    def __init__(self, ref_channel: Channel, eval_channel: Channel, comparison: Comparison) -> None:
        super().__init__()
        self.ref_channel = ref_channel
        self.eval_channel = eval_channel
        repository = ChannelDataRepository()
        self.ref_data = repository.load_from_channel(ref_channel)
        self.eval_data = repository.load_from_channel(eval_channel)
        self.comparison = comparison
        self.sync_processor = SyncProcessor()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Prepare Channel Comparison")
        self.resize(600, 600)
        main_layout = w.QVBoxLayout()
        plot_widget = PlotWidget()

        plot_widget.plot_channel_data(self.ref_data, color=0)
        plot_widget.plot_channel_data(self.eval_data, color=1)

        for i, sync_block in enumerate(self.comparison.sync_blocks):
            plot_widget.plot_vertical_line(
                sync_block.ref_start, color=0)
            plot_widget.plot_vertical_line(
                sync_block.ref_end, color=0, linestyle=':')
            plot_widget.plot_vertical_line(
                sync_block.eval_start, color=1)
            plot_widget.plot_vertical_line(
                sync_block.eval_end, color=1, linestyle=':')

        main_layout.addWidget(plot_widget)

        repo = ChannelRepository()

        description = w.QLabel(repo.get_channel_description(self.ref_channel))
        description.setWordWrap(True)
        description.setLineWidth(600)
        main_layout.addWidget(description)

        main_layout.addWidget(w.QLabel("Synchronize when value reaches:"))
        ref_sync_value_input = w.QLineEdit()
        eval_sync_value_input = w.QLineEdit()

        main_layout.addWidget(ref_sync_value_input)
        main_layout.addWidget(eval_sync_value_input)

        sync_button = w.QPushButton("Synchronize")
        sync_button.clicked.connect(
            lambda: self.handle_sync(ref_sync_value_input.text(), eval_sync_value_input.text()))

        main_layout.addWidget(sync_button)

        reset_sync_button = w.QPushButton("Reset Synchronization")
        reset_sync_button.clicked.connect(self.handle_reset_sync)
        main_layout.addWidget(reset_sync_button)

        utils.update_layout(self, main_layout)

    def handle_sync(self, ref_sync_value: str, eval_sync_value: str):
        try:
            ref_sync_value = float(ref_sync_value)
            eval_sync_value = float(eval_sync_value)
            self.sync_processor.sync(self.comparison,
                                     self.ref_data, self.eval_data, ref_sync_value, eval_sync_value)
            self.init_ui()
        except ValueError:
            w.QMessageBox.warning(self, "Sync Value Error",
                                  "Sync value must be a number", w.QMessageBox.Ok)

    def handle_reset_sync(self):
        self.comparison.sync_blocks = []
        self.init_ui()
