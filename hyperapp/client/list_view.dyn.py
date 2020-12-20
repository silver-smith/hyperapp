import abc
import sys
import logging
import bisect
import weakref
from collections import namedtuple
from functools import partial

from PySide2 import QtCore, QtGui, QtWidgets

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.client.util import uni2str, key_match, key_match_any, make_async_action
from hyperapp.common.logger import log, create_context_task
from hyperapp.client.module import ClientModule

from . import htypes
from .list_object import ListObserver, ListObject
from .layout import MultiItemObjectLayout
from .view import View

_log = logging.getLogger(__name__)


ROW_HEIGHT_PADDING = 3  # same as default QTreeView padding


class _Model(QtCore.QAbstractTableModel):

    def __init__(self, view, columns, object):
        QtCore.QAbstractTableModel.__init__(self)
        self._view_wr = weakref.ref(view)
        self._object = object
        self._columns = columns
        self._key_attr = object.key_attribute
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
        _log.debug('_Model.canFetchMore row=%d column=%r eof=%s', parent.row(), parent.column(), self._eof)
        return not self._eof

    def fetchMore(self, parent):
        _log.debug('_Model.fetchMore row=%d column=%r fetch pending=%s', parent.row(), parent.column(), self._fetch_pending)
        self._fetch_more()

    # ListObserver methods ----------------------------------------------------------------------------------------------

    def process_fetch_results(self, item_list, fetch_finished):
        _log.debug('fetched %d items (finished=%s): %s', len(item_list), fetch_finished, item_list)
        prev_items_len = len(self._item_list)
        self.beginInsertRows(QtCore.QModelIndex(), len(self._item_list), prev_items_len + len(item_list) - 1)
        self._item_list += item_list
        self._id2index.update({
            getattr(item, self._key_attr): self.createIndex(prev_items_len + i, 0)
            for i, item in enumerate(item_list)})
        self.endInsertRows()
        view = self._view_wr()
        if view:
            view._on_data_changed()
        if fetch_finished:
            self._fetch_pending = False
        if fetch_finished and not self._eof and view and view._wanted_current_id is not None:
            # item we want to set as current is not fetched yet
            self._fetch_more()

    def process_eof(self):
        _log.debug('reached eof')
        self._eof = True

    # own methods  ------------------------------------------------------------------------------------------------------

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
        _log.info('  requesting fetch from %r', from_key)
        create_context_task(self._object.fetch_items(from_key), log.fetch_more)
        self._fetch_pending = True

    def index2id(self, index):
        if not index.isValid():
            return None
        item = self._item_list[index.row()]
        return getattr(item, self._key_attr)

    def id2index(self, item_id):
        return self._id2index.get(item_id)

    def __del__(self):
        _log.info('~list_view.Model self=%s', id(self))


class ListViewObserver(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def current_changed(self, current_key):
        pass


class ListView(View, ListObserver, QtWidgets.QTableView):

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

    # obsolete
    def get_state(self):
        return self._data_type('list', self._object.get_state(), self._resource_key, self.current_item_key)

    def get_object(self):
        return self._object

    def add_observer(self, observer):
        self._observers.add(observer)

    def keyPressEvent(self, evt):
        if key_match_any(evt, ['Tab', 'Backtab', 'Ctrl+Tab', 'Ctrl+Shift+Backtab']):
            evt.ignore()  # let splitter or tab view handle it
            return
        QtWidgets.QTableView.keyPressEvent(self, evt)

    def currentChanged(self, idx, prev_idx):
        log.current_changed(row=idx.row())
        QtWidgets.QTableView.currentChanged(self, idx, prev_idx)
        current_key = self.current_item_key
        for observer in self._observers:
            observer.current_changed(current_key)

    # ListObserver methods ----------------------------------------------------------------------------------------------

    def process_fetch_results(self, item_list, fetch_finished):
        self.model().process_fetch_results(item_list, fetch_finished)

    def process_eof(self):
        self.model().process_eof()

    # -------------------------------------------------------------------------------------------------------------------

    @property
    def current_item_key(self):
        return self.model().index2id(self.currentIndex())

    def _on_data_changed(self):
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
        self.setCurrentIndex(index)
        self.scrollTo(index)
        self._wanted_current_id = None

    def _on_activated(self, index):
        if self._default_command:
            create_context_task(self._default_command.run(), log.activated)

    # def __del__(self):
    #     _log.debug('~list_view.ListView self=%r', id(self))


class ListViewLayout(MultiItemObjectLayout):

    @classmethod
    async def from_data(cls, state, path, layout_watcher, ref_registry, async_ref_resolver, resource_resolver):
        object_type = await async_ref_resolver.summon(state.object_type_ref)
        return cls(ref_registry, path, object_type, state.command_list, resource_resolver)

    def __init__(self, ref_registry, path, object_type, command_list_data, resource_resolver):
        super().__init__(ref_registry, path, object_type, command_list_data, resource_resolver)

    @property
    def data(self):
        return htypes.list_view.list_layout(self._object_type_ref, self._command_list_data)

    async def visual_item(self):
        return self.make_visual_item('ListView')

    def _create_view_impl(self, object, columns):
        return ListView(columns, object)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)
        self._ref_registry = services.ref_registry
        services.available_object_layouts.register('list', [ListObject.type._t], self._make_list_layout_data)
        services.default_object_layouts.register('list', [ListObject.type._t], self._make_list_layout_data)
        services.object_layout_registry.register_actor(
            htypes.list_view.list_layout, ListViewLayout.from_data, services.ref_registry, services.async_ref_resolver, services.resource_resolver)

    async def _make_list_layout_data(self, object_type):
        object_type_ref = self._ref_registry.distil(object_type)
        command_list = MultiItemObjectLayout.make_default_command_list(object_type)
        return htypes.list_view.list_layout(object_type_ref, command_list)
