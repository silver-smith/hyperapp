import asyncio
import logging

from PySide import QtCore, QtGui

from hyperapp.client.module import ClientModule
from . import htypes
from .tree_object import TreeObserver, TreeObject
from .view import View

log = logging.getLogger(__name__)


MODULE_NAME = 'tree_view'


class _Model(QtCore.QAbstractItemModel, TreeObserver):

    def __init__(self, resource_resolver, locale, resource_key, object):
        QtCore.QAbstractItemModel.__init__(self)
        TreeObserver.__init__(self)
        self._resource_resolver = resource_resolver
        self._locale = locale
        self._resource_key = resource_key
        self._object = object
        self._columns = object.get_columns()
        self._path2items = {}
        self._id2path = {0: ()}  # root index assume id = 0
        self._path2id = {(): 0}
        self._id_counter = 0
        self._column2resource = {}
        self._object.subscribe(self)

    def index(self, row, column, parent):
        if not parent.isValid():
            return self.createIndex(row, column, 0)
        path = self._id2path[parent.internalId()]
        return self.createIndex(row, column, 0)

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        path = self._id2path[index.internalId()]
        parent_id = self._path2id[path[:-1]]
        return self.createIndex(0, 0, parent_id)

    def columnCount(self, index):
        return len(self._columns)

    def headerData(self, section, orient, role):
        if role == QtCore.Qt.DisplayRole and orient == QtCore.Qt.Orientation.Horizontal:
            column_id = self._columns[section].id
            resource = self._column2resource.get(column_id)
            if resource:
                return resource.text
            else:
                return column_id
        return QtCore.QAbstractTableModel.headerData(self, section, orient, role)

    def rowCount(self, index):
        item_list = self._path2items.get(())
        if item_list:
            return len(item_list)
        path = self._id2path.get(index.internalId())
        if not path:
            return 0
        item_list = self._path2items[path]
        return len(item_list)

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        column = self._columns[index.column()]
        path = self._id2path.get(index.internalId())
        if path is None:
            return None
        item_list = self._path2items[path]
        item = item_list[index.row()]
        value = getattr(item, column.id)
        return str(value)

    def populate(self):
        asyncio.ensure_future(self._object.fetch_items([]))

    def process_fetch_results(self, path, item_list):
        log.debug('tree view: fetched %d items at %s', len(item_list), path)
        self._path2items[tuple(path)] = item_list
        self.rowsInserted.emit(QtCore.QModelIndex(), 1, len(item_list) - 1)


class TreeView(View, QtGui.QTreeView):

    def __init__(self, resource_resolver, locale, parent, resource_key, object):
        QtGui.QTreeView.__init__(self)
        View.__init__(self, parent)
        self.setModel(_Model(resource_resolver, locale, resource_key, object))
        self._object = object

    def setVisible(self, visible):
        QtGui.QTreeView.setVisible(self, visible)
        if visible:
            self.populate()

    def get_state(self):
        return htypes.tree_view.tree_handle('tree', self._object, None)

    def populate(self):
        self.model().populate()
        for idx in range(len(self.model()._columns)):
            self.resizeColumnToContents(idx)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        self._resource_resolver = services.resource_resolver
        services.tree_view_factory = self._tree_view_factory
        services.view_registry.register('tree', self._tree_view_from_state, services.objimpl_registry)

    async def _tree_view_from_state(self, locale, state, parent, objimpl_registry):
        object = await objimpl_registry.resolve_async(state.object)
        return self._tree_view_factory(locale, parent, state.resource_key, object)

    def _tree_view_factory(self, locale, parent, resource_key, object):
        return TreeView(self._resource_resolver, locale, parent, resource_key, object)
