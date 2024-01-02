from PySide6 import QtCore, QtGui, QtWidgets

from .services import (
    ui_adapter_creg,
    )


ROW_HEIGHT_PADDING = 3  # same as default QTreeView padding


class _Model(QtCore.QAbstractTableModel):

    def __init__(self, adapter):
        super().__init__()
        self._adapter = adapter

    # Qt methods  -------------------------------------------------------------------------------------------------------

    def columnCount(self, parent):
        return self._adapter.column_count()

    def headerData(self, section, orient, role):
        if role == QtCore.Qt.DisplayRole and orient == QtCore.Qt.Orientation.Horizontal:
            return self._adapter.column_title(section)
        return super().headerData(section, orient, role)

    def rowCount(self, parent):
        return self._adapter.row_count()

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        return self._adapter.cell_data(index.row(), index.column())


class ListCtl:

    @classmethod
    def from_piece(cls, layout):
        adapter = ui_adapter_creg.invite(layout.adapter)
        return cls(adapter)

    def __init__(self, adapter):
        self._adapter = adapter

    def construct_widget(self, state, ctx):
        widget = QtWidgets.QTableView()
        widget.setModel(_Model(self._adapter))
        widget.verticalHeader().hide()
        widget.setShowGrid(False)
        widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        widget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        font_info = widget.fontInfo()
        widget.verticalHeader().setDefaultSectionSize(font_info.pixelSize() + ROW_HEIGHT_PADDING)
        widget.setCurrentIndex(widget.model().createIndex(0, 0))
        return widget

    def widget_state(self, widget):
        return None

    def get_commands(self, layout, widget, wrapper):
        return []
