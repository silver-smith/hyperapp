import logging

from PySide2 import QtCore, QtGui, QtWidgets

from hyperapp.common.module import Module

from . import htypes
from .list_object import ListObject

log = logging.getLogger(__name__)


ROW_HEIGHT_PADDING = 3  # same as default QTreeView padding


class _Model(QtCore.QAbstractTableModel):

    def __init__(self, view, object, config):
        QtCore.QAbstractTableModel.__init__(self)

    # Qt methods  -------------------------------------------------------------------------------------------------------

    def columnCount(self, parent):
        return 10

    def headerData(self, section, orient, role):
        if role == QtCore.Qt.DisplayRole and orient == QtCore.Qt.Orientation.Horizontal:
            return 'test header'
        return QtCore.QAbstractTableModel.headerData(self, section, orient, role)

    def rowCount(self, parent):
        return 10

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        return 'test'


class ListView(QtWidgets.QTableView):

    @classmethod
    async def from_piece(cls, piece, adapter, origin_dir, lcs):
        config = lcs.slice(adapter.dir_list[-1])
        return cls(adapter, config)

    def __init__(self, object, config, key=None):
        QtWidgets.QTableView.__init__(self)
        self.setModel(_Model(self, object, config))
        self.verticalHeader().hide()
        opts = self.viewOptions()
        self.verticalHeader().setDefaultSectionSize(QtGui.QFontInfo(opts.font).pixelSize() + ROW_HEIGHT_PADDING)
        self.horizontalHeader().setStretchLastSection(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.lcs.set([htypes.view.view_d('default'), htypes.list_object.list_object_d()], htypes.list_view.list_view())
        services.view_registry.register_actor(htypes.list_view.list_view, ListView.from_piece, services.lcs)
