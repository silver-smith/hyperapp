import logging
from collections import namedtuple
from functools import partial

from PySide6 import QtCore, QtGui, QtWidgets

from . import htypes
from .services import (
    ui_adapter_creg,
    )
from .code.list_diff import ListDiff
from .code.view import View

log = logging.getLogger(__name__)


ROW_HEIGHT_PADDING = 3  # same as default QTreeView padding


ModelState = namedtuple('ModelState', 'current_idx current_item')


class _Model(QtCore.QAbstractTableModel):

    def __init__(self, adapter):
        super().__init__()
        self.adapter = adapter
        self.adapter.subscribe(self)

    # Qt methods  -------------------------------------------------------------------------------------------------------

    def columnCount(self, parent):
        return self.adapter.column_count()

    def headerData(self, section, orient, role):
        if role == QtCore.Qt.DisplayRole and orient == QtCore.Qt.Orientation.Horizontal:
            return self.adapter.column_title(section)
        return super().headerData(section, orient, role)

    def rowCount(self, parent):
        return self.adapter.row_count()

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        return self.adapter.cell_data(index.row(), index.column())

    # subscription  ----------------------------------------------------------------------------------------------------

    def process_diff(self, diff):
        log.info("List: process diff: %s", diff)
        if not isinstance(diff, ListDiff.Append):
            raise NotImplementedError(diff)
        row_count = self.adapter.row_count()
        self.beginInsertRows(QtCore.QModelIndex(), row_count - 1, row_count - 1)
        self.endInsertRows()


class _TableView(QtWidgets.QTableView):

    def setVisible(self, visible):
        super().setVisible(visible)
        if visible:
            self.setFocus()


class ListView(View):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.adapter)

    def __init__(self, adapter_ref):
        super().__init__()
        self._adapter_ref = adapter_ref

    @property
    def piece(self):
        return htypes.list.view(self._adapter_ref)

    def construct_widget(self, state, ctx):
        adapter = ui_adapter_creg.invite(self._adapter_ref, ctx)
        widget = _TableView()
        model = _Model(adapter)
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
        adapter = widget.model().adapter
        idx = widget.currentIndex().row()
        if adapter.row_count():
            current_item = adapter.get_item(idx)
        else:
            current_item = None
        return ModelState(current_idx=idx, current_item=current_item)

    def _on_data_changed(self, widget, *args):
        log.info("List: on_data_changed: %s: %s", widget, args)
        widget.resizeColumnsToContents()
