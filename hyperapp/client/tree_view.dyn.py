import abc
import asyncio
from contextlib import suppress
import logging
import weakref

from PySide2 import QtCore, QtWidgets

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.client.util import make_async_action
from hyperapp.client.command import Command
from hyperapp.client.module import ClientModule

from . import htypes
from .tree_object import AppendItemDiff, InsertItemDiff, RemoveItemDiff, TreeObserver, TreeObject
from .view import View
from .view_registry import NotApplicable
from .items_view import map_columns_to_view

log = logging.getLogger(__name__)


class _Model(QtCore.QAbstractItemModel, TreeObserver):

    def __init__(self, view, columns, object):
        QtCore.QAbstractItemModel.__init__(self)
        TreeObserver.__init__(self)
        self._view_wr = weakref.ref(view)
        self._object = object
        self.columns = columns
        self._key_attr = object.key_attribute
        self._path2item = {}
        self._path2children = {}
        self._fetch_requested_for_path = set()  # do not issue fetch request when previous is not yet completed
        self._id2path = {}
        self._path2id = {}
        self._id_counter = 0
        self._object.subscribe(self)

    # qt methods  -------------------------------------------------------------------------------------------------------

    def columnCount(self, index):
        return len(self.columns)

    def headerData(self, section, orient, role):
        if role == QtCore.Qt.DisplayRole and orient == QtCore.Qt.Orientation.Horizontal:
            return self.columns[section].title
        return QtCore.QAbstractTableModel.headerData(self, section, orient, role)

    def index(self, row, column, parent):
        parent_path = self.index2path(parent) or ()
        # log.debug('_Model.index(%s, %s, %s), id=%s, path=%s', row, column, parent, parent.internalId(), parent_path)
        item_list = self._path2children[parent_path]
        key = getattr(item_list[row], self._key_attr)
        path = parent_path + (key,)
        id = self._path2id.get(path)
        if id is None:
            id = self._get_next_id()
            self._path2id[path] = id
            self._id2path[id] = path
        return self.createIndex(row, column, id)

    def parent(self, index):
        path = self.index2path(index)
        if path and len(path) > 1:
            parent_id = self._path2id[path[:-1]]
            return self.createIndex(0, 0, parent_id)
        else:
            return QtCore.QModelIndex()

    def hasChildren(self, index):
        path = self.index2path(index)
        item_list = self._path2children.get(path or ())
        return item_list != []  # is empty item list already received for this path?

    def rowCount(self, index):
        path = self.index2path(index)
        item_list = self._path2children.get(path or ())
        if item_list is None:
            self.request_fetch(path)
            return 0
        else:
            return len(item_list)

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        column = self.columns[index.column()]
        path = self._id2path.get(index.internalId())
        # log.debug('_Model.data id=%d, row=%d column=%r path=%s', index.internalId(), index.row(), index.column(), path)
        if path is None:
            return None
        item = self._path2item[path]
        value = getattr(item, column.id)
        return str(value)

    def canFetchMore(self, parent):
        path = self.index2path(parent)
        result = (path or ()) not in self._path2children
        log.debug('_Model.canFetchMore id=%d, row=%d column=%r path=%s, result=%s', parent.internalId(), parent.row(), parent.column(), path, result)
        return result

    def fetchMore(self, parent):
        path = self.index2path(parent)
        log.debug('_Model.fetchMore id=%d, row=%d column=%r path=%s already fetching=%s',
                  parent.internalId(), parent.row(), parent.column(), path, path in self._fetch_requested_for_path)
        self.request_fetch(path)

    # TreeObserver methods  ---------------------------------------------------------------------------------------------

    def process_fetch_results(self, path, item_list):
        log.debug('fetched %d items at %s: %s', len(item_list), path, item_list)
        path = tuple(path)
        with suppress(KeyError):
            self._fetch_requested_for_path.remove(path or None)
        self._append_items(path, item_list)

    def process_diff(self, path, diff):
        path = tuple(path)
        if isinstance(diff, AppendItemDiff):
            self._append_items(path, [diff.item])
        elif isinstance(diff, InsertItemDiff):
            self._insert_item(path, diff.idx, diff.item)
        elif isinstance(diff, RemoveItemDiff):
            self._remove_item(path)
        else:
            raise RuntimeError(f"Unknown Diff class: {diff}")

    # own methods  ------------------------------------------------------------------------------------------------------

    def _append_items(self, path, item_list):
        current_item_list = self._path2children.setdefault(path, [])
        if not item_list:
            return
        prev_item_count = len(current_item_list)
        current_item_list += item_list
        for item in item_list:
            id = self._get_next_id()
            key = getattr(item, self._key_attr)
            item_path = path + (key,)
            self._path2item[item_path] = item
            self._path2id[item_path] = id
            self._id2path[id] = item_path
        self.rowsInserted.emit(QtCore.QModelIndex(), prev_item_count + 1, len(current_item_list) - 1)
        view = self._view_wr()
        if view:
            view._on_data_changed()

    def _insert_item(self, path, idx, item):
        item_list = self._path2children.setdefault(path, [])
        item_list.insert(idx, item)
        id = self._get_next_id()
        key = getattr(item, self._key_attr)
        item_path = path + (key,)
        self._path2item[item_path] = item
        self._path2id[item_path] = id
        self._id2path[id] = item_path
        self.rowsInserted.emit(QtCore.QModelIndex(), idx + 1, idx + 1)
        view = self._view_wr()
        if view:
            view._on_data_changed()

    def _remove_item(self, path):
        assert path  # Can't remove root item
        parent_path = path[:-1]
        item_list = self._path2children.get(parent_path, [])
        assert item_list, path
        for idx, item in enumerate(item_list):
            key = getattr(item, self._key_attr)
            if key == path[-1]:
                break
        else:
            raise RuntimeError(f"No item at path: {path}")
        index = self.path2index(parent_path) or QtCore.QModelIndex()
        id = self._path2id[path]
        self.beginRemoveRows(index, idx, idx)
        del item_list[idx]
        del self._path2item[path]
        del self._path2id[path]
        del self._id2path[id]
        self.endRemoveRows()

    def request_fetch(self, path):
        if path:
            path = tuple(path)
        if (path or ()) in self._path2children:
            return
        if (path or None) in self._fetch_requested_for_path:
            return
        self._fetch_requested_for_path.add(path or None)
        log.info('  request fetch for %s', path)
        asyncio.ensure_future(self._object.fetch_items(path or []))
    def index2path(self, index):
        if index.isValid():
            return self._id2path[index.internalId()]
        else:
            return None

    def path2index(self, path):
        if not path:
            return None
        path = tuple(path)
        id = self._path2id.get(path)
        if id is None:
            return None
        item_list = self._path2children.get(path[:-1])
        key_list = [getattr(item, self._key_attr) for item in item_list]
        row = key_list.index(path[-1])
        return self.createIndex(row, 0, id)

    def first_row_index(self):
        item_list = self._path2children.get(())
        if not item_list:
            return None
        item_0_key = getattr(item_list[0], self._key_attr)
        id = self._path2id.get((item_0_key,))
        return self.createIndex(0, 0, id)

    def _get_next_id(self):
        self._id_counter += 1
        return self._id_counter


class TreeViewObserver(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def current_changed(self, current_path):
        pass


class TreeView(View, QtWidgets.QTreeView):

    def __init__(self, columns, object, current_path=None):
        self._observers = weakref.WeakSet()
        self._elt_actions = []    # QtGui.QAction list - actions for selected elements
        QtWidgets.QTreeView.__init__(self)
        self.setModel(_Model(self, columns, object))
        View.__init__(self)
        self.setSelectionMode(self.ContiguousSelection)
        self._object = object
        self._wanted_current_path = current_path  # will set it to current when rows are loaded
        self._default_command = None
        self.activated.connect(self._on_activated)
        self.expanded.connect(self._on_expanded)

    # obsolete
    def get_state(self):
        return self._data_type('tree', self._object.get_state(), self._resource_key, self.current_item_path)

    def get_object(self):
        return self._object

    def add_observer(self, observer):
        self._observers.add(observer)

    def currentChanged(self, idx, prev_idx):
        QtWidgets.QTreeView.currentChanged(self, idx, prev_idx)
        current_path = self.current_item_path
        for observer in self._observers:
            observer.current_changed(current_path)

    @property
    def current_item_path(self):
        path = self.model().index2path(self.currentIndex())
        if path is None:
            return None
        else:
            return list(path)

    def _on_data_changed(self):
        self._process_wanted_current()
        # only after some nodes are expanded we can resize columns:
        self._resize_columns_to_contents()

    def _resize_columns_to_contents(self):
        for idx in range(len(self.model().columns)):
            self.resizeColumnToContents(idx)

    def _process_wanted_current(self):
        if self._wanted_current_path is not None:
            index = self.model().path2index(self._wanted_current_path)
            if not index:
                self._fetch_nearest_parent_node(self._wanted_current_path)
        else:
            if self.currentIndex().isValid():
                return
            else:
                index = self.model().first_row_index()
        if index is None:
            return
        for i in range(len(self._wanted_current_path or []) - 1):
            path = self._wanted_current_path[:i + 1]
            self.expand(self.model().path2index(path))
        self.setCurrentIndex(index)
        self.scrollTo(index)
        self._wanted_current_path = None

    def _fetch_nearest_parent_node(self, wanted_path):
        while wanted_path:
            wanted_path = wanted_path[:-1]
            index = self.model().path2index(wanted_path)
            if index:
                log.debug('fetch nearest parent: %s', wanted_path)
                self.model().request_fetch(wanted_path)
                return

    def _on_activated(self, index):
        if self._default_command:
            asyncio.ensure_future(self._default_command.run())

    def _on_expanded(self, index):
        # Some items may be inserted by now, but not still visible.
        self._resize_columns_to_contents()

    def __del__(self):
        log.debug('~tree_view.TreeView self=%r', id(self))


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._type_resolver = services.type_resolver
        self._resource_resolver = services.resource_resolver
        services.tree_view_factory = self._tree_view_factory
        services.view_producer_registry.register_view_producer(self._produce_view)

    def _tree_view_factory(self, columns, object, current_path):
        return TreeView(columns, object, current_path)

    async def _produce_view(self, piece, object, observer):
        if not isinstance(object, TreeObject):
            raise NotApplicable(object)
        type_ref = self._piece_type_ref(piece)
        columns = list(map_columns_to_view(self._resource_resolver, type_ref, object.get_columns()))
        tree_view = TreeView(columns, object)
        if observer:
            tree_view.add_observer(observer)
        return tree_view

    def _piece_type_ref(self, piece):
        t = deduce_value_type(piece)
        return self._type_resolver.reverse_resolve(t)
