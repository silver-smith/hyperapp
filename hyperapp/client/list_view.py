import sys
import logging
import asyncio
import bisect
from PySide import QtCore, QtGui
from ..common.htypes import Type
from .util import uni2str, key_match, key_match_any, make_async_action
from .command import Command, ViewCommand
from .list_object import ListObserver, ListDiff, Slice, ListObject
from . import view

log = logging.getLogger(__name__)


ROW_HEIGHT_PADDING = 3  # same as default QTreeView padding
APPEND_PHONY_REC_COUNT = 2  # minimum 2 for infinite forward scrolling 


def register_views(registry, services):
    registry.register('list', View.from_state, services.types.core, services.objimpl_registry, services.resources_manager)


class Model(QtCore.QAbstractTableModel):

    def __init__(self, locale, resources_manager, resource_id):
        QtCore.QAbstractTableModel.__init__(self)
        self._locale = locale
        self._resources_manager = resources_manager
        self._resource_id = resource_id
        self._fetch_pending = False  # has pending fetch request; do not issue more than one request at a time
        self._object = None
        self._columns = []
        self._columns_resource = {}  # column_id -> tColumnResource
        self._visible_columns = []
        self._key2element = {}
        self._current_order = None  # column id
        self.keys = []  #  ordered elements keys
        self.bof = False
        self.eof = False

    def get_sort_column_id(self):
        return self._current_order

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            column = self._visible_columns[index.column()]
            if index.row() >= len(self.keys):
                return None  # phony row
            key = self.keys[index.row()]
            element = self._get_key_element(key)
            value = getattr(element.row, column.id)
            return self._value_to_string(column, value)
        return None

    def _value_to_string(self, column, value):
        return str(value)

    def headerData(self, section, orient, role):
        if role == QtCore.Qt.DisplayRole and orient == QtCore.Qt.Orientation.Horizontal:
            column_id = self._visible_columns[section].id
            resource = self._column2resource.get(column_id)
            if resource:
                return resource.text
            else:
                return column_id
        return QtCore.QAbstractTableModel.headerData(self, section, orient, role)

    def rowCount(self, parent):
        if parent == QtCore.QModelIndex() and self._object:
            count = len(self.keys)
            if not self.eof:
                count += APPEND_PHONY_REC_COUNT
            return count
        else:
            return 0

    def columnCount(self, parent):
        if parent == QtCore.QModelIndex() and self._object:
            return len(self._visible_columns)
        else:
            return 0

    def reset(self):
        ## self._update_mapping()
        QtCore.QAbstractTableModel.reset(self)

    def set_object(self, object, sort_column_id):
        self._object = object
        self._columns = object.get_columns()
        self._column2resource = {
            column.id: self._resources_manager.resolve(self._resource_id + ['column', column.id, self._locale])
            for column in self._columns}
        self._visible_columns = [column for column in self._columns if self._is_column_visible(column.id)]
        self._key_column_id = object.get_key_column_id()
        self._current_order = sort_column_id or self._current_order
        self.keys = []
        self.eof = False
        self.eof = False
        self.reset()
        self._fetch_pending = False

    def _is_column_visible(self, column_id):
        resource = self._column2resource.get(column_id)
        if resource:
            return resource.visible
        else:
            return True

    def _wanted_last_row(self, first_visible_row, visible_row_count):
        wanted_last_row = first_visible_row + visible_row_count
        if not self.eof:
            wanted_last_row += APPEND_PHONY_REC_COUNT
        return wanted_last_row

    @asyncio.coroutine
    def fetch_elements_if_required(self, first_visible_row, visible_row_count, force=False):
        if self._fetch_pending: return
        wanted_last_row = self._wanted_last_row(first_visible_row, visible_row_count)
        wanted_rows = wanted_last_row - len(self.keys)
        key = self.keys[-1] if self.keys else None
        log.info('-- list_view.Model.fetch_elements_if_required self=%r first_visible_row=%r visible_row_count=%r'
                 ' wanted_last_row=%r len(keys)=%r eof=%r wanted_rows=%r',
                 id(self), first_visible_row, visible_row_count, wanted_last_row, len(self.keys), self.eof, wanted_rows)
        if force or (wanted_rows > 0 and not self.eof):
            log.info('   calling fetch_elements object=%s/%r key=%r wanted_rows=%r', id(self._object), self._object, key, wanted_rows)
            self._fetch_pending = True  # must be set before request because it may callback immediately and so clear _fetch_pending
            yield from self._object.fetch_elements(self._current_order, key, 0, wanted_rows)

    def process_fetch_result(self, slice):
        log.info('-- list_view.Model.process_fetch_result self=%r object=%r len(slice.elements)=%r', id(self), self._object, len(slice.elements))
        self._fetch_pending = False
        old_len = len(self.keys)
        self._update_elements_map(slice.elements)
        if slice.elements:
            idx = bisect.bisect_left(self.keys, slice.elements[0].key)
        else:
            idx = len(self.keys)
        self.keys = self.keys[:idx] + [element.key for element in slice.elements]
        self.eof = slice.eof
        self.rowsInserted.emit(QtCore.QModelIndex(), old_len + 1, old_len + len(slice.elements))
    
    def diff_applied(self, diff):
        start_idx = bisect.bisect_left(self.keys, diff.start_key)
        end_idx = bisect.bisect_right(self.keys, diff.end_key)
        log.info('-- list_view.Model.diff_applied self=%r diff=%r start_idx=%r end_idx=%r len(keys)=%r keys=%r',
                 id(self), diff, start_idx, end_idx, len(self.keys), self.keys)
        for key in self.keys[start_idx:end_idx]:
            del self._key2element[key]
        self._update_elements_map(diff.elements)
        self.keys[start_idx:end_idx] = [element.key for element in diff.elements]
        if end_idx > start_idx:
            self.rowsRemoved.emit(QtCore.QModelIndex(), start_idx, end_idx - 1)
        if len(diff.elements):
            self.rowsInserted.emit(QtCore.QModelIndex(), start_idx, start_idx + len(diff.elements))
        log.info('  > len(keys)=%r keys=%r', len(self.keys), self.keys)

    def get_key_row(self, key):
        try:
            return self.keys.index(key)
        except ValueError:
            return None

    def get_row_key(self, row):
        if row == 0 and not self.keys:
            return None
        return self.keys[row]

    def get_row_element(self, row):
        if row >= len(self.keys):
            return None  # no elements or phony row
        key = self.keys[row]
        return self._get_key_element(key)

    ## def get_visible_slice(self, first_visible_row, visible_row_count):
    ##     last_row = self._wanted_last_row(first_visible_row, visible_row_count)
    ##     if first_visible_row > 0:
    ##         from_key = self.keys[first_visible_row - 1]
    ##     else:
    ##         from_key = None
    ##     elements = [self._get_key_element(key) for key in self.keys[first_visible_row:last_row]]
    ##     bof = self.bof and first_visible_row == 0
    ##     eof = self.eof and last_row >= len(self.keys)
    ##     return Slice(self._current_order, from_key, elements, bof, eof)

    def _update_elements_map(self, elements):
        for element in elements:
            self._key2element[element.key] = element

    def _get_key_element(self, key):
        return self._key2element[key]

    def __del__(self):
        log.info('~list_view.Model self=%s', id(self))


class View(view.View, ListObserver, QtGui.QTableView):

    @classmethod
    @asyncio.coroutine
    def from_state(cls, locale, state, parent, core_types, objimpl_registry, resources_manager):
        data_type = core_types.handle.resolve_obj(state)
        object = objimpl_registry.resolve(state.object)
        return cls(locale, parent, resources_manager, state.resource_id, data_type, object, state.key, state.sort_column_id)

    def __init__(self, locale, parent, resources_manager, resource_id, data_type, object, key, sort_column_id, first_visible_row=None, select_first=True):
        assert parent is None or isinstance(parent, view.View), repr(parent)
        assert data_type is None or isinstance(data_type, Type), repr(data_type)
        assert sort_column_id, repr(sort_column_id)
        log.debug('new list_view self=%s', id(self))
        QtGui.QTableView.__init__(self)
        view.View.__init__(self, parent)
        self._locale = locale
        self._resources_manager = resources_manager
        self._resource_id = resource_id
        self.data_type = data_type
        self._select_first = select_first
        self._object = None
        self.setModel(Model(self._locale, self._resources_manager, self._resource_id))
        self.verticalHeader().hide()
        opts = self.viewOptions()
        self.verticalHeader().setDefaultSectionSize(QtGui.QFontInfo(opts.font).pixelSize() + ROW_HEIGHT_PADDING)
        self.horizontalHeader().setStretchLastSection(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)
        self.verticalScrollBar().valueChanged.connect(self.vscrollValueChanged)
        self.activated.connect(self._on_activated)
        self._elt_commands = []   # Command list - commands for selected elements
        self._elt_actions = []    # QtGui.QAction list - actions for selected elements
#        print (len(slice.elements), slice.eof) if slice else None
        ## if handle_slice:
        ##     object.put_back_slice(handle_slice)
        self.set_object(object, sort_column_id)
        self.wanted_current_key = key  # will set it to current when rows are loaded

    def get_state(self):
        first_visible_row, visible_row_count = self._get_visible_rows()
        ## slice = self.model().get_visible_slice(first_visible_row, visible_row_count)
        return self.data_type('list', self.get_object().get_state(), self._resource_id,
                              self.model().get_sort_column_id(), self.get_current_key())
       #, first_visible_row, self._select_first)

    def get_title(self):
        if self._object:
            return self._object.get_title()

    def get_object(self):
        return self._object

    def get_commands(self, kinds):
        return view.View.get_commands(self, kinds) + self._elt_commands

    def get_sort_column_id(self):
        return self.model().get_sort_column_id()

    def object_changed(self):
        log.info('-- list_view.object_changed self=%s / %r', id(self), self)
        view.View.object_changed(self)
        ## old_key = self._selected_elt.key if self._selected_elt else None
        ## self.model().reset()
        ## ## self.reset()  # selection etc must be cleared
        ## row = self.model().key2row(old_key)
        ## if row is None and self._object.element_count() > 0:
        ##     # find next or any nearby row
        ##     for row, element in enumerate(self._object.get_fetched_elements()):
        ##         if element.key >= old_key:
        ##             break  # use this row
        ##     # else: just use last row
        ## if row is not None:
        ##     self.set_current_row(row)
        ## view.View.object_changed(self)
        ## self.check_if_elements_must_be_fetched()

    def process_fetch_result(self, slice):
        log.debug('-- list_view.process_fetch_result self=%s (pre)', id(self))
        self.model()  # Internal C++ object (View) already deleted - this possible means this view was leaked.
        log.info('-- list_view.process_fetch_result self=%s model=%r sort_column_id=%r bof=%r eof=%r len(elements)=%r',
                 id(self), id(self.model()), slice.sort_column_id, slice.bof, slice.eof, len(slice.elements))
        assert isinstance(slice, Slice), repr(slice)
        self.model().process_fetch_result(slice)
        self.resizeColumnsToContents()
        if self.wanted_current_key is not None:
            if self.set_current_key(self.wanted_current_key):
                self.wanted_current_key = None
        elif self.currentIndex().row() == -1:
            self.set_current_key(select_first=True)
        self.fetch_elements_if_required()

    def diff_applied(self, diff):
        assert isinstance(diff, ListDiff), repr(diff)
        self.model().diff_applied(diff)
        self._selected_elements_changed()

    def get_current_key(self):
        current_elt = self.get_current_elt()
        if not current_elt:
            return None
        return current_elt.key

    def get_current_elt(self):
        index = self.currentIndex()
        if index.row() == -1: return None
        return self.model().get_row_element(index.row())

    def _get_selected_elts(self):
        element = self.get_current_elt()
        if element:
            return [element]
        else:
            return []  # no selection

    def is_in_multi_selection_mode(self):
        return False  # todo

    def set_current_row(self, row):
        if row is None: return
        idx = self.model().createIndex(row, 0)
        self.setCurrentIndex(idx)
        self.scrollTo(idx)
        self._selected_elements_changed()

    def set_current_key(self, key=None, select_first=False, accept_near=False):
        row = self.model().get_key_row(key)
        log.info('-- set_current_key key=%r select_first=%r row=%r keys=%r', key, select_first, row, self.model().keys)
        if row is None:
            if select_first:
                row = 0
            else:
                return False
        self.set_current_row(row)
        ## if accept_near:
        ##     row = self._find_nearest_key(key)
        ## else:
        ##     row = self.model().key2row(key)
        ##     if row is None and select_first and self._object.get_fetched_elements():
        ##         row = 0
        ## if row is None:
        ##     return False
        ## self.set_current_row(row)
        return True

    def _find_nearest_key(self, key):
        for idx, element in enumerate(self._object.get_fetched_elements()):
            if element.key >= key:
                return idx
        if self._object.get_fetched_elements():
            return 0
        else:
            return None  # has no rows

    def selected_keys(self):
        return None

    def set_object(self, object, sort_column_id=None):
        log.info('-- set_object self=%r model=%r object=%r isVisible=%r', id(self), id(self.model()), object, self.isVisible())
        assert isinstance(object, ListObject), repr(object)
        assert sort_column_id is not None or self.model().get_sort_column_id() is not None
        if self._object:
            self._object.unsubscribe(self)
        self._object = object
        self.model().set_object(object, sort_column_id)
        self.resizeColumnsToContents()
        self._object.subscribe(self)
        if self.isVisible():
            self.fetch_elements_if_required()

    def keyPressEvent(self, evt):
        if key_match_any(evt, ['Tab', 'Backtab', 'Ctrl+Tab', 'Ctrl+Shift+Backtab']):
            evt.ignore()  # let splitter or tab view handle it
            return
        QtGui.QTableView.keyPressEvent(self, evt)

    def vscrollValueChanged(self, value):
        self.fetch_elements_if_required()

    def resizeEvent(self, evt):
        log.info('-- resizeEvent self=%r model=%r isVisible=%r visible-rows=%r', id(self), id(self.model()), self.isVisible(), self._get_visible_rows())
        result = QtGui.QTableView.resizeEvent(self, evt)
        # only now we are visible and know how many elements we require
        self.fetch_elements_if_required()
        return result

    def currentChanged(self, idx, prev_idx):
        QtGui.QTableView.currentChanged(self, idx, prev_idx)
        self._selected_elements_changed()

    def setVisible(self, visible):
        log.debug('-- list_view.setVisible self=%s visible=%r', id(self), visible)
        QtGui.QTableView.setVisible(self, visible)
        if visible:
            self.view_commands_changed(['element'])

    def _get_visible_rows(self):
        first_visible_row = self.verticalHeader().visualIndexAt(0)
        row_height = self.verticalHeader().defaultSectionSize()
        visible_row_count = self.viewport().height() // row_height
        return (first_visible_row, visible_row_count)

    def fetch_elements_if_required(self):
        first_visible_row, visible_row_count = self._get_visible_rows()
        asyncio.async(self.model().fetch_elements_if_required(first_visible_row, visible_row_count, force=self.wanted_current_key is not None))

    ## def check_if_elements_must_be_fetched(self):
    ##     last_visible_row = self.get_last_visible_row()
    ##     want_element_count = last_visible_row + 1
    ##     force_load = self.want_current_key is not None
    ##     self._object.need_elements_count(last_visible_row + 1, force_load)

    def _on_activated(self, index):
        element = self.model().get_row_element(index.row())
        for cmd in element.commands:
            resource = self._resources_manager.resolve(cmd.resource_id + [self._locale])
            if resource and resource.is_default:
                break
        else:
            return
        asyncio.async(self._wrap_element_command(element, cmd).run())

    def _selected_elements_changed(self):
        self._update_selected_actions()
        if self.isVisible():  # we may being destructed now
            self.view_commands_changed(['element'])

    def _wrap_element_command(self, element, cmd):
        return ViewCommand.from_command(cmd.clone(args=(element.key,)), self)

    def _update_selected_actions(self):
        # remove previous actions
        action_widget = self
        for action in self._elt_actions:
            action_widget.removeAction(action)
        self._elt_actions = []
        self._elt_commands = []
        # pick selection and commands
        element = self.get_current_elt()
        if not element: return
        # create actions
        for cmd in element.commands:
            assert isinstance(cmd, Command), repr(cmd)
            assert cmd.kind == 'element', repr(cmd)
            resource = self._resources_manager.resolve(cmd.resource_id + [self._locale])
            wrapped_cmd = self._wrap_element_command(element, cmd)
            action = make_async_action(
                action_widget, '%s/%s' % (wrapped_cmd.resource_id, wrapped_cmd.id),
                resource.shortcuts if resource else None, wrapped_cmd.run)
            action.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
            action_widget.addAction(action)
            self._elt_actions.append(action)
            self._elt_commands.append(wrapped_cmd)

    def __del__(self):
        log.debug('~list_view.View self=%r', id(self))
