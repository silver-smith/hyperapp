import asyncio
import logging
import time
from functools import partial

from PySide6 import QtCore, QtWidgets

from . import htypes
from .code.mark import mark
from .code.view import View
from .code.tree_visual_diff import VisualTreeDiffAppend, VisualTreeDiffInsert, VisualTreeDiffReplace

log = logging.getLogger(__name__)


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
        try:
            id = index.internalId() or 0
            return self.adapter.has_children(id)
        except:
            log.exception("Error in Tree model hasChildren:")
            return False

    def rowCount(self, parent):
        parent_id = parent.internalId() or 0
        return self.adapter.row_count(parent_id)

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        id = index.internalId() or 0
        value = self.adapter.cell_data(id, index.column())
        if value is None:
            return ""
        else:
            return str(value)

    # subscription  ----------------------------------------------------------------------------------------------------

    def process_diff(self, diff):
        log.info("Tree: process diff: %s", diff)
        if not isinstance(diff, (VisualTreeDiffAppend, VisualTreeDiffInsert, VisualTreeDiffReplace)):
            raise NotImplementedError(diff)
        if isinstance(diff, VisualTreeDiffAppend):
            row = self.adapter.row_count(diff.parent_id)
        else:
            row = diff.idx
        if diff.parent_id:
            parent_idx = self.createIndex(row + 1, 0, diff.parent_id)
        else:
            parent_idx = QtCore.QModelIndex()
        # VisualTreeDiffReplace: self.dataChanged.emit does not cause qt to recheck rowCount.
        log.info("Tree: insert rows: %s", parent_idx)
        if isinstance(diff, VisualTreeDiffReplace):
            self.beginRemoveRows(parent_idx, 0, 0)
            self.endRemoveRows()
        else:
            # When inserting children into items having none, this is required for them to appear:
            self.layoutAboutToBeChanged.emit()
        self.beginInsertRows(parent_idx, 0, 0)
        self.endInsertRows()
        if not isinstance(diff, VisualTreeDiffReplace):
            self.layoutChanged.emit()


class _TreeWidget(QtWidgets.QTreeView):

    def __init__(self, current_path):
        super().__init__()
        self._want_current_path = current_path
        self.on_state_changed = None
        self._visible_time = 0

    def currentChanged(self, current, previous):
        result = super().currentChanged(current, previous)
        if self.on_state_changed:
            self.on_state_changed()
        return result

    def setVisible(self, visible):
        super().setVisible(visible)
        if visible:
            self.setFocus()
            self._setup()
            self._visible_time = time.time()

    def check_is_just_shown(self):
        # Heuristics to detect initial data population.
        if time.time() - self._visible_time > 1:
            self._want_current_path = None
            return
        self._setup()

    def _setup(self):
        self._initial_expand()
        if self._want_current_path:
            if self._set_current_path(self._want_current_path):
                self._want_current_path = None

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

    def _set_current_path(self, path):
        model = self.model()
        index = self.rootIndex()
        succeeded = True
        while path:
            if not model.hasChildren(index):
                succeeded = False
                break
            if not self.isExpanded(index):
                self.expand(index)
            row = path[0]
            if row >= model.rowCount(index):
                succeeded = False
                break
            parent = index
            index = model.index(row, 0, index)
            path = path[1:]
        # Call later otherwise only first cell is selected, not whole row.
        def select():
            self.setCurrentIndex(index)
            self.scrollTo(index)
        asyncio.get_running_loop().call_soon(select)
        return succeeded  # If true, we are fully expanded and selected.


class TreeView(View):

    @classmethod
    @mark.view
    def from_piece(cls, piece, model, ctx, ui_adapter_creg):
        adapter = ui_adapter_creg.invite(piece.adapter, model, ctx)
        return cls(piece.adapter, adapter)

    def __init__(self, adapter_ref, adapter):
        super().__init__()
        self._adapter_ref = adapter_ref
        self._adapter = adapter

    @property
    def piece(self):
        return htypes.tree.view(self._adapter_ref)

    def construct_widget(self, state, ctx):
        if isinstance(state, htypes.tree.state):
            current_path = state.current_path
        else:
            current_path = None
        widget = _TreeWidget(current_path)
        model = _Model(self._adapter)
        widget.setModel(model)
        widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        widget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        widget.setUniformRowHeights(True)
        for idx in range(self._adapter.column_count()):
            widget.header().setSectionResizeMode(idx, QtWidgets.QHeaderView.ResizeToContents)
        font_info = widget.fontInfo()
        # widget.setCurrentIndex(widget.model().createIndex(0, 0))
        # model.dataChanged.connect(partial(self._on_data_changed, widget))
        model.rowsInserted.connect(partial(self._on_row_inserted, widget))
        return widget

    def init_widget(self, widget):
        widget.on_state_changed = self._ctl_hook.parent_context_changed

    def widget_state(self, widget):
        index = widget.currentIndex()
        item_id = index.internalId()
        path = self._adapter.get_path(item_id)
        return htypes.tree.state(current_path=tuple(path))

    def primary_parent_context(self, rctx, widget):
        return rctx.clone_with(
            model_state=self._model_state(widget),
            )

    def _model_state(self, widget):
        index = widget.currentIndex()
        item_id = index.internalId()
        item = self._adapter.get_item(item_id)
        path = self._adapter.get_path(item_id)
        return self._adapter.model_state_t(current_path=tuple(path), current_item=item)

    @property
    def adapter(self):
        return self._adapter

    def _on_row_inserted(self, widget, parent, first, last):
        log.info("Tree: row inserted: %s: %s %s %s", widget, parent, first, last)
        widget.check_is_just_shown()
