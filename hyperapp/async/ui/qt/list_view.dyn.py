import abc
import asyncio
import sys
import logging
import bisect
import weakref
from bisect import bisect_left
from collections import namedtuple
from functools import partial

from PySide2 import QtCore, QtGui, QtWidgets

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.module import Module

from . import htypes
from .list_object import ListFetcher, ListObserver, ListObject
from .items_view import map_columns_to_view
from .util import uni2str, key_match, key_match_any
from .view import View

log = logging.getLogger(__name__)


ROW_HEIGHT_PADDING = 3  # same as default QTreeView padding


class _Model(QtCore.QAbstractTableModel, ListFetcher):

    def __init__(self, view, columns, object):
        QtCore.QAbstractTableModel.__init__(self)
        self._view_wr = weakref.ref(view)
        self._object = object
        self._columns = columns
        self._key_attr = object.key_attribute
        self._init_data()

    def _init_data(self):
        self._fetch_pending = False  # has pending fetch request; do not issue more than one request at a time
        self._item_list = []
        self._eof = False
        self._id2index = {}

    # qt methods  -------------------------------------------------------------------------------------------------------

    def columnCount(self, parent):
        return len(self._columns)

    def headerData(self, section, orient, role):
        if role == QtCore.Qt.DisplayRole and orient == QtCore.Qt.Orientation.Horizontal:
            return self._columns[section].title
        return QtCore.QAbstractTableModel.headerData(self, section, orient, role)

    def rowCount(self, parent):
        return len(self._item_list)

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        column = self._columns[index.column()]
        item = self._item_list[index.row()]
        value = getattr(item, column.id)
        if value is None:
            return ''
        else:
            return str(value)

    def canFetchMore(self, parent):
        log.debug('_Model.canFetchMore row=%d column=%r eof=%s', parent.row(), parent.column(), self._eof)
        return not self._eof

    def fetchMore(self, parent):
        log.debug('_Model.fetchMore row=%d column=%r fetch pending=%s', parent.row(), parent.column(), self._fetch_pending)
        self._fetch_more()

    def update(self):
        self.beginResetModel()
        self._init_data()
        self.endResetModel()
        self._fetch_more()

    # ListFetcher methods ----------------------------------------------------------------------------------------------=

    def process_fetch_results(self, item_list, fetch_finished):
        log.debug('fetched %d items (finished=%s): %s', len(item_list), fetch_finished, item_list)
        prev_items_len = len(self._item_list)
        self.beginInsertRows(QtCore.QModelIndex(), len(self._item_list), prev_items_len + len(item_list) - 1)
        self._item_list += item_list
        self._id2index.update({
            getattr(item, self._key_attr): self.createIndex(prev_items_len + i, 0)
            for i, item in enumerate(item_list)})
        self.endInsertRows()
        view = self._view_wr()
        if view:
            view._on_data_fetched()
        if fetch_finished:
            self._fetch_pending = False
        if fetch_finished and not self._eof and view and view._wanted_current_id is not None:
            # item we want to set as current is not fetched yet
            self._fetch_more()

    def process_eof(self):
        log.debug('reached eof')
        self._eof = True

    # own methods  ------------------------------------------------------------------------------------------------------

    def process_diff(self, diff):
        log.debug("Process diff: %s", diff)
        current_keys = [getattr(item, self._key_attr) for item in self._item_list]
        for key in diff.remove_keys:
            try:
                idx = current_keys.index(key)
            except ValueError:
                continue
            self.beginRemoveRows(QtCore.QModelIndex(), idx, idx + 1)
            del self._item_list[idx]
            del self._id2index[key]
            del current_keys[idx]
            self.endRemoveRows()
        for item in diff.items:
            key = getattr(item, self._key_attr)
            idx = bisect_left(current_keys, key)
            self.beginInsertRows(QtCore.QModelIndex(), idx, idx + 1)
            self._item_list.insert(idx, item)
            self._id2index[key] = self.createIndex(idx, 0)
            self.endInsertRows()
        view = self._view_wr()
        if view:
            view._on_data_changed()

    def has_rows(self):
        return bool(self._item_list)

    def _fetch_more(self):
        assert not self._eof
        if self._fetch_pending:
            return
        if self._item_list:
            from_key = getattr(self._item_list[-1], self._key_attr)
        else:
            from_key = None
        log.info('  requesting fetch from %r', from_key)
        asyncio.ensure_future(self._object.fetch_items(from_key, self))
        self._fetch_pending = True

    def index2id(self, index):
        if not index.isValid():
            return None
        item = self._item_list[index.row()]
        return getattr(item, self._key_attr)

    def id2index(self, item_id):
        return self._id2index.get(item_id)

    def __del__(self):
        log.info('~list_view.Model self=%s', id(self))


class ListViewObserver(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def current_changed(self, current_key):
        pass


class ListView(View, ListObserver, QtWidgets.QTableView):

    @classmethod
    async def from_piece(cls, piece, object, origin_dir, lcs):
        columns = list(map_columns_to_view(lcs, object))
        return cls(columns, object)

    def __init__(self, columns, object, key=None):
        self._observers = weakref.WeakSet()
        self._elt_actions = []    # QtGui.QAction list - actions for selected elements
        QtWidgets.QTableView.__init__(self)
        self.setModel(_Model(self, columns, object))
        View.__init__(self)
        self._object = object
        self._wanted_current_id = key  # will set it to current when rows are loaded
        self._default_command = None
        self.verticalHeader().hide()
        opts = self.viewOptions()
        self.verticalHeader().setDefaultSectionSize(QtGui.QFontInfo(opts.font).pixelSize() + ROW_HEIGHT_PADDING)
        self.horizontalHeader().setStretchLastSection(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)
        self.activated.connect(self._on_activated)
        self._object.subscribe(self)

    @property
    def piece(self):
        return htypes.list_view.list_view()

    @property
    def state(self):
        current_key = self.current_item_key
        if current_key is None:
            return None  # Happens when widget is not visible.
        return self._object.State(current_key=current_key)

    @state.setter
    def state(self, state):
        if not isinstance(state, self._object.State):
            return  # Happens when another view is configured for an object.
        self._wanted_current_id = state.current_key  # Will set it to current when rows are loaded.

    @property
    def object(self):
        return self._object

    def add_observer(self, observer):
        self._observers.add(observer)

    def keyPressEvent(self, evt):
        if key_match_any(evt, ['Tab', 'Backtab', 'Ctrl+Tab', 'Ctrl+Shift+Backtab']):
            evt.ignore()  # let splitter or tab view handle it
            return
        QtWidgets.QTableView.keyPressEvent(self, evt)

    def currentChanged(self, idx, prev_idx):
        QtWidgets.QTableView.currentChanged(self, idx, prev_idx)
        current_key = self.current_item_key
        for observer in self._observers:
            observer.current_changed(current_key)

    # ObjectObserver methods  -------------------------------------------------------------------------------------------

    def object_changed(self):
        log.debug('ListView.object_changed %s', self)
        View.object_changed(self)
        self._wanted_current_id = self.current_item_key  # will set it to current when rows are reloaded
        self.model().update()

    # ListObserver methods  ---------------------------------------------------------------------------------------------

    def process_diff(self, diff):
        self.model().process_diff(diff)

    # -------------------------------------------------------------------------------------------------------------------

    @property
    def current_item_key(self):
        return self.model().index2id(self.currentIndex())

    def _on_data_changed(self):
        self.resizeColumnsToContents()

    def _on_data_fetched(self):
        self.resizeColumnsToContents()
        if self._wanted_current_id is not None:
            index = self.model().id2index(self._wanted_current_id)
        else:
            if self.currentIndex().isValid():
                return
            elif self.model().has_rows():
                # ensure at least one item is selected
                index = self.model().createIndex(0, 0)
            else:
                return
        if index is not None:  # Already fetched wanted index?
            self.setCurrentIndex(index)
            self.scrollTo(index)
            self._wanted_current_id = None

    def _on_activated(self, index):
        if self._default_command:
            asyncio.ensure_future(self._default_command.run())

    # def __del__(self):
    #     log.debug('~list_view.ListView self=%r', id(self))


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.lcs.set([htypes.view.view_d('default'), *ListObject.dir_list[-1]], htypes.list_view.list_view())
        services.available_view_registry.add_view(ListObject.dir_list[-1], htypes.list_view.list_view())
        services.view_registry.register_actor(htypes.list_view.list_view, ListView.from_piece, services.lcs)
