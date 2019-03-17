import asyncio
from contextlib import suppress
import logging
import weakref

from PySide import QtCore, QtGui

from hyperapp.client.module import ClientModule
from . import htypes
from .tree_object import TreeObserver, TreeObject
from .view import View

log = logging.getLogger(__name__)


MODULE_NAME = 'tree_view'


class _Model(QtCore.QAbstractItemModel, TreeObserver):

    def __init__(self, view, resource_resolver, locale, resource_key, object):
        QtCore.QAbstractItemModel.__init__(self)
        TreeObserver.__init__(self)
        self._view_wr = weakref.ref(view)
        self._resource_resolver = resource_resolver
        self._locale = locale
        self._resource_key = resource_key
        self._object = object
        self._columns = object.get_columns()
        self._item_id_attr = self._columns[0].id
        self._path2item = {}
        self._path2children = {}
        self._fetch_requested_for_path = set()  # do not issue fetch request when previous is not yet completed
        self._id2path = {}
        self._path2id = {}
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
        parent_path = self._index2path(parent)
        log.debug('_Model.index(%s, %s, %s), id=%s, path=%s', row, column, parent, parent.internalId(), parent_path)
        item_list = self._path2children[parent_path]
        id = getattr(item_list[row], self._item_id_attr)
        path = parent_path + (id,)
        id = self._path2id.get(path)
        if id is None:
            id = self._get_next_id()
            self._path2id[path] = id
            self._id2path[id] = path
        return self.createIndex(row, column, id)

    def parent(self, index):
        path = self._index2path(index)
        if path and len(path) > 1:
            parent_id = self._path2id[path[:-1]]
            return self.createIndex(0, 0, parent_id)
        else:
            return QtCore.QModelIndex()

    def hasChildren(self, index):
        return True

    def rowCount(self, index):
        path = self._index2path(index)
        item_list = self._path2children.get(path)
        if item_list is None:
            self._request_fetch(path)
            return 0
        else:
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

    def canFetchMore(self, parent):
        path = self._index2path(parent)
        result = path not in self._path2children
        log.debug('_Model.canFetchMore id=%d, row=%d column=%r path=%s, result=%s', parent.internalId(), parent.row(), parent.column(), path, result)
        return result

    def fetchMore(self, parent):
        path = self._index2path(parent)
        log.debug('_Model.fetchMore id=%d, row=%d column=%r path=%s already fetching=%s',
                  parent.internalId(), parent.row(), parent.column(), path, path in self._fetch_requested_for_path)
        self._request_fetch(path)

    # own methods  ------------------------------------------------------------------------------------------------------

    def _request_fetch(self, path):
        if path not in self._fetch_requested_for_path:
            self._fetch_requested_for_path.add(path)
            log.info('  request fetch for %s', path)
            asyncio.ensure_future(self._object.fetch_items(path))

    def process_fetch_results(self, path, item_list):
        log.debug('fetched %d items at %s: %s', len(item_list), path, item_list)
        path = tuple(path)
        with suppress(KeyError):
            self._fetch_requested_for_path.remove(path)
        self._path2children[path] = item_list
        for item in item_list:
            id = getattr(item, self._item_id_attr)
            self._path2item[path + (id,)] = item
        self.rowsInserted.emit(QtCore.QModelIndex(), 1, len(item_list) - 1)
        for idx in range(len(self._columns)):
            self._view_wr().resizeColumnToContents(idx)

    def _index2path(self, index):
        if index.isValid():
            return self._id2path[index.internalId()]
        else:
            return ()

    def _get_next_id(self):
        self._id_counter += 1
        return self._id_counter


class TreeView(View, QtGui.QTreeView):

    def __init__(self, resource_resolver, locale, parent, resource_key, object):
        QtGui.QTreeView.__init__(self)
        View.__init__(self, parent)
        self.setSelectionMode(self.ContiguousSelection)
        self.setModel(_Model(self, resource_resolver, locale, resource_key, object))
        self._object = object

    def get_state(self):
        return htypes.tree_view.tree_handle('tree', self._object, None)


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
