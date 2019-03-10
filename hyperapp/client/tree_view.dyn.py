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
        self._item_id_attr = self._columns[0].id
        self._path2item = {}
        self._path2children = {}
        self._id2path = {0: ()}  # root index assume id = 0
        self._path2id = {(): 0}
        self._id_counter = 0
        self._column2resource = {}
        self._object.subscribe(self)

    # qt methods  -------------------------------------------------------------------------------------------------------

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

    def index(self, row, column, parent):
        log.debug('_Model.index(%s, %s, %s), valid=%s, id=%s', row, column, parent, parent.isValid(), parent.internalId())
        if not parent.isValid():
            path = ()
        else:
            path = self._id2path[parent.internalId()]
        item_list = self._path2children[path]
        id_attr = self._columns[0].id  # first column is always id
        id = getattr(item_list[row], id_attr)
        path = path + (id,)
        id = self._path2id.get(path)
        if id is None:
            id = self._get_next_id()
            self._path2id[path] = id
            self._id2path[id] = path
        return self.createIndex(0, column, id)

    def parent(self, index):
        path = self._id2path[index.internalId()]
        if not path:
            return QtCore.QModelIndex()
        parent_id = self._path2id[path[:-1]]
        return self.createIndex(0, 0, parent_id)

    def hasChildren(self, index):
        return True

    def rowCount(self, index):
        item_list = self._path2children.get(())
        if item_list:
            return len(item_list)
        path = self._id2path.get(index.internalId())
        if not path:
            return 0
        item_list = self._path2children[path]
        return len(item_list)

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        column = self._columns[index.column()]
        path = self._id2path.get(index.internalId())
        log.debug('_Model.data id=%d, row=%d column=%r path=%s', index.internalId(), index.row(), index.column(), path)
        if path is None:
            return None
        item = self._path2item[path]
        value = getattr(item, column.id)
        return str(value)

    # own methods  ------------------------------------------------------------------------------------------------------

    def populate(self):
        asyncio.ensure_future(self._object.fetch_items([]))

    def process_fetch_results(self, path, item_list):
        log.debug('tree view: fetched %d items at %s', len(item_list), path)
        self._path2children[tuple(path)] = item_list
        for item in item_list:
            id = getattr(item, self._item_id_attr)
            self._path2item[tuple(path) + (id,)] = item
        self.rowsInserted.emit(QtCore.QModelIndex(), 1, len(item_list) - 1)

    def _get_next_id(self):
        self._id_counter += 1
        return self._id_counter


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
