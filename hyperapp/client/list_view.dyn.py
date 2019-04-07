import sys
import logging
import asyncio
import bisect
import weakref

from PySide import QtCore, QtGui

from hyperapp.common.util import single
from hyperapp.common.htypes import Type, resource_key_t
from hyperapp.client.util import uni2str, key_match, key_match_any, make_async_action
from hyperapp.client.command import Command
from hyperapp.client.module import ClientModule
from . import htypes
from .view import ViewCommand, View
from .list_object import ListObserver, ListObject

log = logging.getLogger(__name__)


MODULE_NAME = 'list_view'

ROW_HEIGHT_PADDING = 3  # same as default QTreeView padding


class _Model(QtCore.QAbstractTableModel, ListObserver):

    def __init__(self, view, resource_resolver, locale, resource_key, object):
        QtCore.QAbstractTableModel.__init__(self)
        self._view_wr = weakref.ref(view)
        self._resource_resolver = resource_resolver
        self._locale = locale
        self._resource_key = resource_key
        self._object = object
        self._columns = object.get_columns()
        self._item_id_attr = single(column.id for column in self._columns if column.is_key)
        self._column2resource = {}
        self._fetch_pending = False  # has pending fetch request; do not issue more than one request at a time
        self._item_list = []
        self._eof = False
        self._id2index = {}
        self._load_resources()
        self._object.subscribe(self)

    # qt methods  -------------------------------------------------------------------------------------------------------

    def columnCount(self, parent):
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

    def rowCount(self, parent):
        return len(self._item_list)

    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        column = self._columns[index.column()]
        item = self._item_list[index.row()]
        value = getattr(item, column.id)
        return str(value)

    def canFetchMore(self, parent):
        log.debug('_Model.canFetchMore row=%d column=%r eof=%s', parent.row(), parent.column(), self._eof)
        return not self._eof

    def fetchMore(self, parent):
        log.debug('_Model.fetchMore row=%d column=%r fetch pending=%s', parent.row(), parent.column(), self._fetch_pending)
        self._fetch_more()

    # own methods  ------------------------------------------------------------------------------------------------------

    def _load_resources(self):
        for column in self._columns:
            resource_key = resource_key_t(self._resource_key.module_ref, self._resource_key.path + ['column', column.id])
            self._column2resource[column.id] = self._resource_resolver.resolve(resource_key, self._locale)

    def _fetch_more(self):
        assert not self._eof
        if self._fetch_pending:
            return
        if self._item_list:
            from_key = getattr(self._item_list[-1], self._item_id_attr)
        else:
            from_key = None
        log.info('  requesting fetch from %r', from_key)
        asyncio.ensure_future(self._object.fetch_items(from_key))
        self._fetch_pending = True

    def process_fetch_results(self, item_list, fetch_finished):
        log.debug('fetched %d items (finished=%s): %s', len(item_list), fetch_finished, item_list)
        prev_items_len = len(self._item_list)
        self.beginInsertRows(QtCore.QModelIndex(), len(self._item_list), prev_items_len + len(item_list) - 1)
        self._item_list += item_list
        self._id2index.update({
            getattr(item, self._item_id_attr): self.createIndex(prev_items_len + i, 0)
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
        log.debug('reached eof')
        self._eof = True

    def index2id(self, index):
        if not index.isValid():
            return None
        item = self._item_list[index.row()]
        return getattr(item, self._item_id_attr)

    def id2index(self, item_id):
        return self._id2index.get(item_id)

    def __del__(self):
        log.info('~list_view.Model self=%s', id(self))


class ListView(View, ListObserver, QtGui.QTableView):

    def __init__(self, resource_resolver, locale, parent, resource_key, data_type, object, key):
        assert parent is None or isinstance(parent, View), repr(parent)
        assert data_type is None or isinstance(data_type, Type), repr(data_type)
        QtGui.QTableView.__init__(self)
        self.setModel(_Model(self, resource_resolver, locale, resource_key, object))
        View.__init__(self, parent)
        self._resource_resolver = resource_resolver
        self._locale = locale
        self._resource_key = resource_key
        self._data_type = data_type
        self._object = object
        self._wanted_current_id = key  # will set it to current when rows are loaded
        self._elt_commands = []   # Command list - commands for selected elements
        self._elt_actions = []    # QtGui.QAction list - actions for selected elements
        self._default_command = None
        self.verticalHeader().hide()
        opts = self.viewOptions()
        self.verticalHeader().setDefaultSectionSize(QtGui.QFontInfo(opts.font).pixelSize() + ROW_HEIGHT_PADDING)
        self.horizontalHeader().setStretchLastSection(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)
        self.activated.connect(self._on_activated)

    def get_state(self):
        return self._data_type('list', self._object.get_state(), self._resource_key, self._current_item_id)

    def get_object(self):
        return self._object

    def get_command_list(self, kinds):
        command_list = View.get_command_list(self, kinds)
        filtered_command_list = list(filter(lambda command: command.kind != 'element', command_list))
        if not kinds or 'element' in kinds:
            return filtered_command_list + self._elt_commands
        else:
            return filtered_command_list

    def keyPressEvent(self, evt):
        if key_match_any(evt, ['Tab', 'Backtab', 'Ctrl+Tab', 'Ctrl+Shift+Backtab']):
            evt.ignore()  # let splitter or tab view handle it
            return
        QtGui.QTableView.keyPressEvent(self, evt)

    def currentChanged(self, idx, prev_idx):
        QtGui.QTableView.currentChanged(self, idx, prev_idx)
        self._selected_elements_changed()

    @property
    def _current_item_id(self):
        return self.model().index2id(self.currentIndex())

    def _on_data_changed(self):
        self.resizeColumnsToContents()
        if self._wanted_current_id is None:
            return
        index = self.model().id2index(self._wanted_current_id)
        if index is None:
            return
        self.setCurrentIndex(index)
        self.scrollTo(index)
        self._wanted_current_id = None

    def _on_activated(self, index):
        if self._default_command:
            asyncio.ensure_future(self._default_command.run())

    def _selected_elements_changed(self):
        self._update_selected_actions()
        if self.isVisible():  # we may being destructed now
            self.view_commands_changed(['element'])

    def _update_selected_actions(self):
        # remove previous actions
        action_widget = self
        for action in self._elt_actions:
            action_widget.removeAction(action)
        self._elt_actions.clear()
        self._elt_commands.clear()
        self._default_command = None
        # pick selection and commands
        item_id = self._current_item_id
        if item_id is None:
            return
        # create actions
        for command in self._object.get_item_command_list(item_id):
            assert isinstance(command, Command), repr(command)
            assert command.kind == 'element', repr(command)
            resource = self._resource_resolver.resolve(command.resource_key, self._locale)
            wrapped_command = self._wrap_item_command(item_id, command)
            action = make_async_action(
                action_widget, '%s/%s' % (wrapped_command.resource_key, wrapped_command.id),
                resource.shortcut_list if resource else None, wrapped_command.run)
            action.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
            action_widget.addAction(action)
            self._elt_actions.append(action)
            self._elt_commands.append(wrapped_command)
            if resource.is_default:
                self._default_command = wrapped_command

    def _wrap_item_command(self, item_id, command):
        return ViewCommand.from_command(command, self, item_id)

    def __del__(self):
        log.debug('~list_view.ListView self=%r', id(self))


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        self._resource_resolver = services.resource_resolver
        services.list_view_factory = self._list_view_factory
        services.view_registry.register('list', self._list_view_from_state, services.objimpl_registry)

    async def _list_view_from_state(self, locale, state, parent, objimpl_registry):
        data_type = htypes.core.handle.get_object_class(state)
        object = await objimpl_registry.resolve_async(state.object)
        return self._list_view_factory(locale, parent, state.resource_key, data_type, object, state.key)

    def _list_view_factory(self, locale, parent, resource_key, data_type, object, key):
        return ListView(self._resource_resolver, locale, parent, resource_key, data_type, object, key)
