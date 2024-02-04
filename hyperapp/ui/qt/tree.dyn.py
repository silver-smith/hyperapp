import logging
from collections import namedtuple
from functools import partial

from PySide6 import QtCore, QtGui, QtWidgets

from .services import (
    ui_adapter_creg,
    )

log = logging.getLogger(__name__)


ModelState = namedtuple('ModelState', 'current_idx')


class _Model(QtCore.QAbstractItemModel):

    def __init__(self, adapter):
        super().__init__()
        self._adapter = adapter
        self._adapter.subscribe(self)
        self._id_to_index = {}

    # Qt methods  -------------------------------------------------------------------------------------------------------

    def columnCount(self, parent):
        return self._adapter.column_count()

    def headerData(self, section, orient, role):
        if role == QtCore.Qt.DisplayRole and orient == QtCore.Qt.Orientation.Horizontal:
            return self._adapter.column_title(section)
        return super().headerData(section, orient, role)

    def index(self, row, column, parent):
        parent_id = parent.internalId() or 0
        id = self._adapter.row_id(parent_id, row)
        return self.createIndex(row, column, id)

    def parent(self, index):
        id = index.internalId() or 0
        parent_id = self._adapter.parent_id(id)
        if parent_id == 0:  # It already was parent.
            return QtCore.QModelIndex()
        return self.createIndex(0, 0, parent_id)

    def hasChildren(self, index):
        id = index.internalId() or 0
        return self._adapter.has_children(id)

    def rowCount(self, parent):
        parent_id = parent.internalId() or 0
        return self._adapter.row_count(parent_id)

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        id = index.internalId() or 0
        return self._adapter.cell_data(id, index.column())


class _TreeWidget(QtWidgets.QTreeView):

    def setVisible(self, visible):
        super().setVisible(visible)
        if visible:
            self.setFocus()


class TreeView:

    @classmethod
    def from_piece(cls, layout):
        return cls()

    def construct_widget(self, piece, state, ctx):
        adapter = ui_adapter_creg.invite(piece.adapter, ctx)
        widget = _TreeWidget()
        model = _Model(adapter)
        widget.setModel(model)
        widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        widget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        font_info = widget.fontInfo()
        # widget.setCurrentIndex(widget.model().createIndex(0, 0))
        # model.dataChanged.connect(partial(self._on_data_changed, widget))
        model.rowsInserted.connect(partial(self._on_data_changed, widget))
        return widget

    def get_current(self, piece, widget):
        return None

    def set_on_current_changed(self, widget, on_changed):
        pass

    def widget_state(self, piece, widget):
        return None

    def model_state(self, widget):
        return ModelState(current_idx=widget.currentIndex().row())

    def _on_data_changed(self, widget, *args):
        log.info("Tree: on_data_changed: %s: %s", widget, args)
        widget.resizeColumnsToContents()
