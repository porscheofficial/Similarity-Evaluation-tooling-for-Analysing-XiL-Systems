from typing import Self
from PySide6 import QtCore, QtWidgets, QtGui


class MainView(QtWidgets.QWidget):

    def __new__(cls) -> Self:
        if not hasattr(cls, 'instance'):
            cls.instance = super(MainView, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        super().__init__()

        # Set up the main layout
        self.layout = QtWidgets.QVBoxLayout(self)

        # Create the TabWidget
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)

        # Create the label
        self.label = QtWidgets.QLabel("Select file to show info")
        self.label.setAlignment(QtCore.Qt.AlignCenter)

        # Add widgets to the layout
        self.layout.addWidget(self.tab_widget)
        self.layout.addWidget(self.label)

        # Check if tabs are present
        self.update_label_visibility()

    def close_tab(self, index):
        self.tab_widget.removeTab(index)
        self.update_label_visibility()

    def update_label_visibility(self):
        if self.tab_widget.count() == 0:
            self.label.show()
            self.tab_widget.hide()
        else:
            self.label.hide()
            self.tab_widget.show()

    def open_tab(self, title, widget):
        tab_content = QtWidgets.QWidget()
        tab_layout = QtWidgets.QVBoxLayout(tab_content)
        tab_layout.addWidget(widget)
        self.tab_widget.addTab(tab_content, title)
        self.tab_widget.setCurrentWidget(tab_content)
        self.update_label_visibility()
