import logging
from collections import namedtuple
from functools import partial

from PySide6 import QtCore, QtGui, QtWidgets

from . import htypes
from .services import (
    ui_adapter_creg,
    )
from .code.view import View

log = logging.getLogger(__name__)


ModelState = namedtuple('ModelState', 'current_item')
VisualTreeDiffAppend = namedtuple('VisualTreeDiffAppend', 'parent_id')


class _Model(QtCore.QAbstractItemModel):

    def __init__(self, adapter):
        super().__init__()
        self.adapter = adapter
        self.adapter.subscribe(self)
        self._id_to_index = {}

    # Qt methods  -------------------------------------------------------------------------------------------------------

    def columnCount(self, parent):
        return self.adapter.column_count()

    def headerData(self, section, orient, role):
        if role == QtCore.Qt.DisplayRole and orient == QtCore.Qt.Orientation.Horizontal:
            return self.adapter.column_title(section)
        return super().headerData(section, orient, role)

    def index(self, row, column, parent):
        parent_id = parent.internalId() or 0
        id = self.adapter.row_id(parent_id, row)
        return self.createIndex(row, column, id)

    def parent(self, index):
        id = index.internalId() or 0
        parent_id = self.adapter.parent_id(id)
        if parent_id == 0:  # It already was parent.
            return QtCore.QModelIndex()
        return self.createIndex(0, 0, parent_id)

    def hasChildren(self, index):
        id = index.internalId() or 0
        return self.adapter.has_children(id)

    def rowCount(self, parent):
        parent_id = parent.internalId() or 0
        return self.adapter.row_count(parent_id)

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        id = index.internalId() or 0
        return self.adapter.cell_data(id, index.column())

    # subscription  ----------------------------------------------------------------------------------------------------

    def process_diff(self, diff):
        log.info("Tree: process diff: %s", diff)
        if not isinstance(diff, VisualTreeDiffAppend):
            raise NotImplementedError(diff)
        row_count = self.adapter.row_count(diff.parent_id)
        if diff.parent_id:
            index = self.createIndex(0, 0, diff.parent_id)
        else:
            index = QtCore.QModelIndex()
        self.beginInsertRows(index, row_count - 1, row_count - 1)
        self.endInsertRows()


class _TreeWidget(QtWidgets.QTreeView):

    def __init__(self, on_state_changed):
        super().__init__()
        self._on_state_changed = on_state_changed

    def currentChanged(self, current, previous):
        result = super().currentChanged(current, previous)
        self._on_state_changed()
        return result

    def setVisible(self, visible):
        super().setVisible(visible)
        if visible:
            self.setFocus()
            self._initial_expand()

    def _initial_expand(self):
        def bottom(idx):
            return self.visualRect(idx).bottom()

        model = self.model()
        root = self.rootIndex()
        queue = [root]
        lowest = None
        row_height = None
        height = self.size().height()
        while queue:
            index = queue.pop(0)
            if index is not root and not row_height:
                row_height = self.visualRect(index).height()
            row_count = model.rowCount(index)
            if not row_count:
                continue
            if lowest and row_height and bottom(lowest) + row_height * (row_count + 1) > height:
                break
            self.expand(index)
            for row in range(row_count):
                kid = model.index(row, 0, index)
                queue.append(kid)
            if not lowest or bottom(kid) > bottom(lowest):
                lowest = kid
        self.resizeColumnToContents(0)


class TreeView(View):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.adapter)

    def __init__(self, adapter_ref):
        super().__init__()
        self._adapter_ref = adapter_ref

    @property
    def piece(self):
        return htypes.tree.view(self._adapter_ref)

    def construct_widget(self, state, ctx):
        adapter = ui_adapter_creg.invite(self._adapter_ref, ctx)
        widget = _TreeWidget(self._ctl_hook.state_changed)
        model = _Model(adapter)
        widget.setModel(model)
        widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        widget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        widget.setUniformRowHeights(True)
        font_info = widget.fontInfo()
        # widget.setCurrentIndex(widget.model().createIndex(0, 0))
        # model.dataChanged.connect(partial(self._on_data_changed, widget))
        model.rowsInserted.connect(partial(self._on_data_changed, widget))
        return widget

    def widget_state(self, widget):
        return None

    def model_state(self, widget):
        adapter = widget.model().adapter
        index = widget.currentIndex()
        item = adapter.get_item(index.internalId())
        return ModelState(current_item=item)

    def _on_data_changed(self, widget, *args):
        log.info("Tree: on_data_changed: %s: %s", widget, args)
        # widget.resizeColumnToContents(0)
