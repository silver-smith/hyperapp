import sys
import bisect
from PySide import QtCore, QtGui
from .util import uni2str, key_match, key_match_any
from .list_object import ListObserver, ListDiff, Slice, ListObject
from .command import run_element_command, make_element_cmd_action
from .view_registry import view_registry
from . import view


ROW_HEIGHT_PADDING = 3  # same as default QTreeView padding
APPEND_PHONY_REC_COUNT = 2  # minimum 2 for infinite forward scrolling 


class Handle(view.Handle):

    @classmethod
    def decode( cls, server, contents ):
        return cls(server.resolve_object(contents.object), contents.key)

    def __init__( self, object, key=None, sort_column_id=None,
                  first_visible_row=None, slice=None, select_first=True ):
        assert isinstance(object, ListObject), repr(object)
        assert slice is None or isinstance(slice, Slice), repr(slice)
        view.Handle.__init__(self)
        self.object = object
        self.key = key
        self.sort_column_id = sort_column_id
        self.first_visible_row = first_visible_row
        self.slice = slice  # cached elements slice
        self.select_first = select_first  # bool

    def get_object( self ):
        return self.object

    def construct( self, parent ):
        print 'list_view construct', parent, self.object.get_title(), self.object, repr(self.key)
        return View(parent, self.object, self.key, self.sort_column_id,
                    self.first_visible_row, self.slice, self.select_first)

    def __repr__( self ):
        return 'list_view.Handle(%s, %s)' % (uni2str(self.object.get_title()), uni2str(self.key))


class Model(QtCore.QAbstractTableModel):

    def __init__( self ):
        QtCore.QAbstractTableModel.__init__(self)
        self._fetch_pending = False  # has pending fetch request; do not issue more than one request at a time
        self._object = None
        self._columns = []
        self._visible_columns = []
        self._key2element = {}
        self._current_order = None  # column id
        self.keys = []  #  ordered elements keys
        self.bof = False
        self.eof = False

    def get_sort_column_id( self ):
        return self._current_order

    def data( self, index, role ):
        if role == QtCore.Qt.DisplayRole:
            column = self._visible_columns[index.column()]
            if index.row() >= len(self.keys):
                return None  # phony row
            key = self.keys[index.row()]
            element = self._get_key_element(key)
            value = getattr(element.row, column.id)
            return column.type.to_string(value)
        return None

    def headerData( self, section, orient, role ):
        if role == QtCore.Qt.DisplayRole and orient == QtCore.Qt.Orientation.Horizontal:
            return self._visible_columns[section].title
        return QtCore.QAbstractTableModel.headerData(self, section, orient, role)

    def rowCount( self, parent ):
        if parent == QtCore.QModelIndex() and self._object:
            count = len(self.keys)
            if not self.eof:
                count += APPEND_PHONY_REC_COUNT
            return count
        else:
            return 0

    def columnCount( self, parent ):
        if parent == QtCore.QModelIndex() and self._object:
            return len(self._visible_columns)
        else:
            return 0

    def reset( self ):
        ## self._update_mapping()
        QtCore.QAbstractTableModel.reset(self)

    def set_object( self, object, sort_column_id, slice ):
        self._object = object
        self._columns = object.get_columns()
        self._visible_columns = filter(lambda column: column.title is not None, self._columns)
        self._key_column_id = object.get_key_column_id()
        self._current_order = sort_column_id or self._current_order
        self.keys = []
        self.eof = False
        self.eof = False
        if slice and slice.sort_column_id == self._current_order:
            self._update_elements(slice.elements)
            self.keys = [element.key for element in slice.elements]
            self.bof = slice.bof
            self.eof = slice.eof
        self.reset()
        self._fetch_pending = False

    def _wanted_last_row( self, first_visible_row, visible_row_count ):
        wanted_last_row = first_visible_row + visible_row_count
        if not self.eof:
            wanted_last_row += APPEND_PHONY_REC_COUNT
        return wanted_last_row

    def fetch_elements_if_required( self, first_visible_row, visible_row_count ):
        if self._fetch_pending: return
        wanted_last_row = self._wanted_last_row(first_visible_row, visible_row_count)
        wanted_rows = wanted_last_row - len(self.keys)
        key = self.keys[-1] if self.keys else None
        print '-- list_view.Model.fetch_elements_if_required', id(self), first_visible_row, visible_row_count, wanted_last_row, len(self.keys), self.eof, wanted_rows
        if wanted_rows > 0 and not self.eof:
            print '   fetch_elements', self._object, `key`, wanted_rows
            self._fetch_pending = True  # must be set before request because it may callback immediately and so clear _fetch_pending
            self._object.fetch_elements(self._current_order, key, 'asc', wanted_rows)

    def subscribe_and_fetch_elements( self, observer, first_visible_row, visible_row_count ):
        if self._fetch_pending: return
        wanted_last_row = self._wanted_last_row(first_visible_row, visible_row_count)
        wanted_rows = wanted_last_row
        key = None
        print '-- list_view.Model.subscribe_and_fetch_elements', id(self), self._object, first_visible_row, visible_row_count, wanted_rows
        self._fetch_pending = True  # must be set before request because it may callback immediately and so clear _fetch_pending
        requested = self._object.subscribe_and_fetch_elements(observer, self._current_order, key, 'asc', wanted_rows)
        if not requested:
            self._fetch_pending = False

    def process_fetch_result( self, result ):
        print '-- list_view.Model.process_fetch_result', id(self), self._object, len(result.elements)
        self._fetch_pending = False
        old_len = len(self.keys)
        self._update_elements(result.elements)
        if result.elements:
            idx = bisect.bisect_left(self.keys, result.elements[0].key)
        else:
            idx = len(self.keys)
        self.keys = self.keys[:idx] + [element.key for element in result.elements]
        self.eof = result.eof
        self.rowsInserted.emit(QtCore.QModelIndex(), old_len + 1, old_len + len(result.elements))
    
    def diff_applied( self, diff ):
        start_idx = bisect.bisect_left(self.keys, diff.start_key)
        end_idx = bisect.bisect_right(self.keys, diff.end_key)
        print '-- list_view.Model.diff_applied', id(self), diff, start_idx, end_idx, len(self.keys), self.keys
        for key in self.keys[start_idx:end_idx]:
            del self._key2element[key]
        self._update_elements(diff.elements)
        self.keys[start_idx:end_idx] = [element.key for element in diff.elements]
        if end_idx > start_idx:
            self.rowsRemoved.emit(QtCore.QModelIndex(), start_idx, end_idx - 1)
        if len(diff.elements):
            self.rowsInserted.emit(QtCore.QModelIndex(), start_idx, start_idx + len(diff.elements))
        print '  > ', len(self.keys), self.keys

    def get_key_row( self, key ):
        try:
            return self.keys.index(key)
        except ValueError:
            return None

    def get_row_key( self, row ):
        if row == 0 and not self.keys:
            return None
        return self.keys[row]

    def get_row_element( self, row ):
        if row >= len(self.keys):
            return None  # no elements or phony row
        key = self.keys[row]
        return self._get_key_element(key)

    def get_visible_slice( self, first_visible_row, visible_row_count ):
        last_row = self._wanted_last_row(first_visible_row, visible_row_count)
        if first_visible_row > 0:
            from_key = self.keys[first_visible_row - 1]
        else:
            from_key = None
        elements = [self._get_key_element(key) for key in self.keys[first_visible_row:last_row]]
        bof = self.bof and first_visible_row == 0
        eof = self.eof and last_row >= len(self.keys)
        return Slice(self._current_order, from_key, 'asc', elements, bof, eof)

    def _update_elements( self, elements ):
        for element in elements:
            self._key2element[element.key] = element

    def _get_key_element( self, key ):
        return self._key2element[key]

    def __del__( self ):
        print '~list_view.Model', self


class View(view.View, ListObserver, QtGui.QTableView):

    def __init__( self, parent, object, key, sort_column_id, first_visible_row, handle_slice, select_first ):
        QtGui.QTableView.__init__(self)
        view.View.__init__(self, parent)
        self._select_first = select_first
        self._object = None
        self.setModel(Model())
        self.verticalHeader().hide()
        opts = self.viewOptions()
        self.verticalHeader().setDefaultSectionSize(QtGui.QFontInfo(opts.font).pixelSize() + ROW_HEIGHT_PADDING)
        self.horizontalHeader().setStretchLastSection(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)
        self.verticalScrollBar().valueChanged.connect(self.vscrollValueChanged)
        self.activated.connect(self._on_activated)
        self._elt_actions = []    # QtGui.QAction list - actions for selected elements
        self._subscribed = False
        if not sort_column_id:
            sort_column_id = object.get_default_sort_column_id()
        self.set_object(object, sort_column_id, handle_slice)
        self.set_current_key(key, select_first)

    def handle( self ):
        first_visible_row, visible_row_count = self._get_visible_rows()
        slice = self.model().get_visible_slice(first_visible_row, visible_row_count)
        return Handle(self.get_object(), self.get_current_key(), self.model().get_sort_column_id(),
                      first_visible_row, slice, self._select_first)

    def get_title( self ):
        if self._object:
            return self._object.get_title()

    def get_object( self ):
        return self._object

    def object_changed( self ):
        print '-- list_view.object_changed', self
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

    def process_fetch_result( self, result ):
        print '-- process_fetch_result', self, id(self.model()), result.sort_column_id, result.bof, result.eof, len(result.elements)
        assert isinstance(result, Slice), repr(result)
        self.model().process_fetch_result(result)
        self.resizeColumnsToContents()
        self.fetch_elements_if_required()

    def diff_applied( self, diff ):
        assert isinstance(diff, ListDiff), repr(diff)
        self.model().diff_applied(diff)
        self._selected_elements_changed()

    def get_current_key( self ):
        current_elt = self.get_current_elt()
        if not current_elt:
            return None
        return current_elt.key

    def get_current_elt( self ):
        index = self.currentIndex()
        if index.row() == -1: return None
        return self.model().get_row_element(index.row())

    def get_selected_elts( self ):
        element = self.get_current_elt()
        if element:
            return [element]
        else:
            return []  # no selection

    def is_in_multi_selection_mode( self ):
        return False  # todo

    def set_current_row( self, row ):
        if row is None: return
        idx = self.model().createIndex(row, 0)
        self.setCurrentIndex(idx)
        self.scrollTo(idx)

    def set_current_key( self, key, select_first=False, accept_near=False ):
        row = self.model().get_key_row(key)
        print '-- set_current_key', `key`, select_first, `row`
        if row is None and select_first:
            row = 0
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

    def _find_nearest_key( self, key ):
        for idx, element in enumerate(self._object.get_fetched_elements()):
            if element.key >= key:
                return idx
        if self._object.get_fetched_elements():
            return 0
        else:
            return None  # has no rows

    def selected_keys( self ):
        return None

    def set_object( self, object, sort_column_id=None, slice=None ):
        print '-- set_object', self, id(self.model()), object, self.isVisible(), (len(slice.elements), slice.eof) if slice else None
        assert isinstance(object, ListObject), repr(object)
        assert sort_column_id is not None or self.model().get_sort_column_id() is not None
        assert isinstance
        if self._object and self._subscribed:
            self._object.unsubscribe_local(self)
        self._object = object
        self.model().set_object(object, sort_column_id, slice)
        self.resizeColumnsToContents()
        if self.isVisible():
            first_visible_row, visible_row_count = self._get_visible_rows()
            self.model().subscribe_and_fetch_elements(self, first_visible_row, visible_row_count)
            self._subscribed = True
        else:
            self._subscribed = False

    def keyPressEvent( self, evt ):
        if key_match_any(evt, ['Tab', 'Backtab', 'Ctrl+Tab', 'Ctrl+Shift+Backtab']):
            evt.ignore()  # let splitter or tab view handle it
            return
        QtGui.QTableView.keyPressEvent(self, evt)

    def vscrollValueChanged( self, value ):
        self.fetch_elements_if_required()

    def resizeEvent( self, evt ):
        print '-- resizeEvent', self, id(self.model()), self.isVisible(), self._get_visible_rows()
        result = QtGui.QTableView.resizeEvent(self, evt)
        if self._subscribed:
            self.fetch_elements_if_required()
        else:
            # we need proper visible row/count for subscribe_and_fetch_elements, got them only in resizeEvent
            first_visible_row, visible_row_count = self._get_visible_rows()
            self.model().subscribe_and_fetch_elements(self, first_visible_row, visible_row_count)
            self._subscribed = True
        return result

    def currentChanged( self, idx, prev_idx ):
        QtGui.QTableView.currentChanged(self, idx, prev_idx)
        self._selected_elements_changed()

    def setVisible( self, visible ):
        QtGui.QTableView.setVisible(self, visible)
        if visible:
            self.selected_elements_changed(self.get_selected_elts())

    def _get_visible_rows( self ):
        first_visible_row = self.verticalHeader().visualIndexAt(0)
        row_height = self.verticalHeader().defaultSectionSize()
        visible_row_count = self.viewport().height() / row_height
        return (first_visible_row, visible_row_count)

    def fetch_elements_if_required( self ):
        first_visible_row, visible_row_count = self._get_visible_rows()
        self.model().fetch_elements_if_required(first_visible_row, visible_row_count)

    ## def check_if_elements_must_be_fetched( self ):
    ##     last_visible_row = self.get_last_visible_row()
    ##     want_element_count = last_visible_row + 1
    ##     force_load = self.want_current_key is not None
    ##     self._object.need_elements_count(last_visible_row + 1, force_load)

    def _on_activated( self, index ):
        element = self.model().get_row_element(index.row())
        for cmd in element.commands:
            if cmd.id == 'open':
                run_element_command(cmd, self, element.key)
                return

    def _selected_elements_changed( self ):
        self._update_selected_actions()
        if self.isVisible():  # we may being destructed now
            self.selected_elements_changed(self.get_selected_elts())

    def _update_selected_actions( self ):
        # remove previous actions
        action_widget = self
        for action in self._elt_actions:
            action_widget.removeAction(action)
        self._elt_actions = []
        # pick selection and commands
        element = self.get_current_elt()
        if not element: return
        # create actions
        for cmd in element.commands:
            action = make_element_cmd_action(cmd, action_widget, self, element.key)
            action.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
            action_widget.addAction(action)
            self._elt_actions.append(action)

    def __del__( self ):
        print '~list_view.View', self


view_registry.register('list', Handle.decode)
