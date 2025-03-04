import PySide6.QtWidgets as w


class SelectMultipleDialog(w.QDialog):
    """A dialog window for selecting multiple items from a list.
    This dialog presents a list of options where the user can select multiple items
    using checkboxes. It includes OK and Cancel buttons to confirm or cancel the selection.
    Args:
        options (list[str]): A list of strings to be displayed as selectable options.
        parent (QWidget, optional): The parent widget. Defaults to None.
    Methods:
        getSelection(): Returns a list of strings containing the text of selected items.
    Example:
        dialog = SelectMultipleDialog(['Option 1', 'Option 2', 'Option 3'])
        if dialog.exec():
            selected_items = dialog.getSelection()
    """

    def __init__(self, options: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Multiple")
        self.main_layout = w.QVBoxLayout()

        self.list_widget = w.QListWidget()

        self.list_widget.setSelectionMode(
            w.QAbstractItemView.SelectionMode.MultiSelection)

        self.list_widget.addItems(options)

        self.main_layout.addWidget(self.list_widget)

        self.button_box = w.QDialogButtonBox(
            w.QDialogButtonBox.Ok | w.QDialogButtonBox.Cancel, self)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.main_layout.addWidget(self.button_box)

        self.setLayout(self.main_layout)

    def getSelection(self):
        return [item.text() for item in self.list_widget.selectedItems()]
