import logging
from types import SimpleNamespace

from PySide2 import QtCore, QtGui, QtWidgets

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


ROW_HEIGHT_PADDING = 3  # same as default QTreeView padding


class _Model(QtCore.QAbstractTableModel):

    def __init__(self, view, adapter, config):
        QtCore.QAbstractTableModel.__init__(self)
        self._adapter = adapter

    # Qt methods  -------------------------------------------------------------------------------------------------------

    def columnCount(self, parent):
        return len(self._adapter.columns)

    def headerData(self, section, orient, role):
        if role == QtCore.Qt.DisplayRole and orient == QtCore.Qt.Orientation.Horizontal:
            return self._adapter.columns[section]
        return QtCore.QAbstractTableModel.headerData(self, section, orient, role)

    def rowCount(self, parent):
        return self._adapter.row_count

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        row = self._adapter.row(index.row())
        name = self._adapter.columns[index.column()]
        return row[name]

    def canFetchMore(self, parent):
        return self._adapter.can_fetch_more()

    def fetchMore(self, parent):
        return self._adapter.fetch_more()


class ListView(QtWidgets.QTableView):

    @classmethod
    async def from_piece(cls, piece, adapter, origin_dir, lcs):
        config = lcs.slice(adapter.dir_list[-1])
        return cls(adapter, config)

    def __init__(self, adapter, config, key=None):
        QtWidgets.QTableView.__init__(self)
        self._adapter = adapter
        self.setModel(_Model(self, adapter, config))
        self.verticalHeader().hide()
        opts = self.viewOptions()
        self.verticalHeader().setDefaultSectionSize(QtGui.QFontInfo(opts.font).pixelSize() + ROW_HEIGHT_PADDING)
        self.horizontalHeader().setStretchLastSection(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)

    @property
    def state(self):
        idx = self.currentIndex().row()
        if idx == -1:
            return None  # No row is selected.
        current_key = self._adapter.idx_to_id[idx]
        if current_key is None:
            return None  # Happens when widget is not visible.
        return self._adapter.state_t(current_key)

    @state.setter
    def state(self, state):
        if state is None:
            return
        try:
            idx = self._adapter.id_to_idx[state.current_key]
        except KeyError:
            return  # No such name: list contents changes, it's ok.
        index = self.model().createIndex(idx, 0)
        self.setCurrentIndex(index)

    @property
    def current_item(self):
        idx = self.currentIndex().row()
        if idx == -1:
            return None  # No row is selected.
        row = self._adapter.row(idx)
        return SimpleNamespace(**row)

    def setVisible(self, visible):
        super().setVisible(visible)
        if visible:
            self.resizeColumnsToContents()


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.lcs.set([htypes.view.view_d('default'), htypes.list.list_d()], htypes.list_view.list_view())
        services.view_registry.register_actor(htypes.list_view.list_view, ListView.from_piece, services.lcs)
