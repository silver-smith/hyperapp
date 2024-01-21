import logging
from collections import namedtuple
from functools import partial

from PySide6 import QtCore, QtGui, QtWidgets

from .services import (
    ui_adapter_creg,
    )
from .code.list_diff import ListDiffAppend

log = logging.getLogger(__name__)


ROW_HEIGHT_PADDING = 3  # same as default QTreeView padding


ModelState = namedtuple('ModelState', 'current_idx')


class _Model(QtCore.QAbstractTableModel):

    def __init__(self, adapter):
        super().__init__()
        self._adapter = adapter
        self._adapter.subscribe(self)

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

    # subscription  ----------------------------------------------------------------------------------------------------

    def process_diff(self, diff):
        log.info("List: process diff: %s", diff)
        if not isinstance(diff, ListDiffAppend):
            raise NotImplementedError(diff)
        row_count = self._adapter.row_count()
        self.beginInsertRows(QtCore.QModelIndex(), row_count - 1, row_count - 1)
        self.endInsertRows()


class ListCtl:

    @classmethod
    def from_piece(cls, layout):
        adapter = ui_adapter_creg.invite(layout.adapter)
        return cls(adapter)

    def __init__(self, adapter):
        self._adapter = adapter

    def construct_widget(self, state, ctx):
        widget = QtWidgets.QTableView()
        model = _Model(self._adapter)
        widget.setModel(model)
        widget.verticalHeader().hide()
        widget.setShowGrid(False)
        widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        widget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        font_info = widget.fontInfo()
        widget.verticalHeader().setDefaultSectionSize(font_info.pixelSize() + ROW_HEIGHT_PADDING)
        widget.setCurrentIndex(widget.model().createIndex(0, 0))
        widget.resizeColumnsToContents()
        # model.dataChanged.connect(partial(self._on_data_changed, widget))
        model.rowsInserted.connect(partial(self._on_data_changed, widget))
        return widget

    def widget_state(self, widget):
        return None

    def model_state(self, widget):
        return ModelState(current_idx=widget.currentIndex().row())

    def get_commands(self, layout, widget, wrapper):
        return []

    def _on_data_changed(self, widget, *args):
        log.info("List: on_data_changed: %s: %s", widget, args)
        widget.resizeColumnsToContents()
