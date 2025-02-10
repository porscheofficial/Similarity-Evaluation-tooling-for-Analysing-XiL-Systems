from PySide6 import QtCore, QtWidgets, QtGui


class LoadingIndicator(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 200)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedSize(100, 50)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Loading..."))
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.change_progress)
        self.timer.start(100)

    def change_progress(self):
        value = self.progress_bar.value()
        value += 1
        if value > 100:
            value = 0
        self.progress_bar.setValue(value)
