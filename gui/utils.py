from PySide6 import QtWidgets, QtCore


def delete_layout(layout: QtWidgets.QLayout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                delete_layout(item.layout())
        layout.deleteLater()


def update_layout(widget: QtWidgets.QWidget, new_layout: QtWidgets.QLayout):
    layout = widget.layout()
    delete_layout(layout)
    QtCore.QTimer.singleShot(0, lambda: widget.setLayout(new_layout))


def update_ui(widget: QtWidgets.QWidget, setup_ui):
    layout = widget.layout()
    delete_layout(layout)
    QtCore.QTimer.singleShot(0, lambda: setup_ui())


def crop_text_end(text: str, length: int = 20) -> str:
    if len(text) > length:
        return "..." + text[-length:]
    return text
