import sys
from PySide import QtCore, QtGui

sys.path.append('..')

from util import uni2str, key_match, key_match_any
from list_object import ListDiff
import view_registry
import view


ROW_HEIGHT_PADDING = 3  # same as default QTreeView padding


class Handle(view.Handle):

    @classmethod
    def from_resp( cls, obj, resp ):
        selected_key = resp.get('selected_key')
        return cls(obj, key=selected_key, select_first=False)

    def __init__( self, obj, key=None, selected_keys=None, select_first=True ):
        view.Handle.__init__(self)
        self.obj = obj
        self.key = key
        self.selected_keys = selected_keys  # for multi-select mode only
        self.select_first = select_first  # bool

    def get_object( self ):
        return self.obj

    def construct( self, parent ):
        print 'list_view construct', parent, self.obj.get_title(), self.obj, repr(self.key)
        return View(parent, self.obj, self.key, self.selected_keys, self.select_first)

    def __repr__( self ):
        return 'list_view.Handle(%s, %s)' % (uni2str(self.obj.get_title()), uni2str(self.key))


class Model(QtCore.QAbstractTableModel):

    def __init__( self ):
        QtCore.QAbstractTableModel.__init__(self)
        self._list_obj = None
        self._visible_columns = []
        self._key2row = {}

    def element_count( self ):
        return self._list_obj.element_count()

    def elements_added( self, added_count ):
        element_count = self._list_obj.element_count()
        self.rowsInserted.emit(QtCore.QModelIndex(), element_count - added_count, element_count - 1)

    def diff_applied( self, diff ):
        if diff.start_key == None and diff.end_key == None:  # append
            self._update_mapping()
            self.elements_added(len(diff.elements))

    def data( self, index, role ):
        if role == QtCore.Qt.DisplayRole:
            element = self._list_obj.get_fetched_elements()[index.row()]
            column = self._visible_columns[index.column()]
            return column.type.to_string(element.row[column.idx])
        return None

    def headerData( self, section, orient, role ):
        if role == QtCore.Qt.DisplayRole and orient == QtCore.Qt.Orientation.Horizontal:
            return self._visible_columns[section].title
        hdata = QtCore.QAbstractTableModel.headerData(self, section, orient, role)
        return hdata

    def rowCount( self, parent ):
        if parent == QtCore.QModelIndex() and self._list_obj:
            return self._list_obj.element_count()
        else:
            return 0

    def columnCount( self, parent ):
        if parent == QtCore.QModelIndex() and self._list_obj:
            return len(self._visible_columns)
        else:
            return 0

    def reset( self ):
        self._update_mapping()
        QtCore.QAbstractTableModel.reset(self)

    def set_object( self, list_obj ):
        self._list_obj = list_obj
        self._visible_columns = filter(lambda column: column.title is not None, list_obj.get_columns())
        self.reset()

    def key2row( self, key ):
        return self._key2row.get(key)

    def _update_mapping( self ):
        self._key2row = {}
        for row, element in enumerate(self._list_obj.get_fetched_elements()):
            self._key2row[element.key] = row

    def __del__( self ):
        print '~list_view.Model'


class View(view.View, QtGui.QTableView):

    def __init__( self, parent, obj, key, selected_keys, select_first ):
        QtGui.QTableView.__init__(self)
        view.View.__init__(self, parent)
        self._select_first = select_first
        self.list_obj = None
        self._model = Model()
        self.setModel(self._model)
        self.verticalHeader().hide()
        opts = self.viewOptions()
        self.verticalHeader().setDefaultSectionSize(QtGui.QFontInfo(opts.font).pixelSize() + ROW_HEIGHT_PADDING)
        self.horizontalHeader().setStretchLastSection(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)
        self.verticalScrollBar().valueChanged.connect(self.vscrollValueChanged)
        self.activated.connect(self._on_activated)
        self._selected_elt = None  # must keep own reference because it may change/disappear independently
        self._elt_actions = []    # QtGui.QAction list - actions for selected elements
        self.want_current_key = None
        self.set_object(obj)
        if not self.set_current_key(key, select_first):
            self.want_current_key = key  # need to fetch elements until this key is fount

    def handle( self ):
        return Handle(self.get_object(), self.get_current_key(), self.selected_keys(), self._select_first)

    def get_title( self ):
        if self.list_obj:
            return self.list_obj.get_title()

    def get_object( self ):
        return self.list_obj

    def object_changed( self ):
        old_key = self._selected_elt.key
        self.model().reset()
        ## self.reset()  # selection etc must be cleared
        row = self.model().key2row(old_key)
        if row is None and self.list_obj.element_count() > 0:
            # find next or any nearby row
            for row, element in enumerate(self.list_obj.get_fetched_elements()):
                if element.key >= old_key:
                    break  # use this row
            # else: just use last row
        if row is not None:
            self.set_current_row(row)
        view.View.object_changed(self)

    def diff_applied( self, diff ):
        assert isinstance(diff, ListDiff), repr(diff)
        self._model.diff_applied(diff)
        self._find_wanted_current_key()
        # may be this was response from elements fetching, but we may need more elements
        self.check_if_elements_must_be_fetched()

    def _find_wanted_current_key( self ):
        if self.set_current_key(self.want_current_key):
            self.want_current_key = None

    def get_current_key( self ):
        if self._selected_elt:
            return self._selected_elt.key
        else:
            return None

    def get_current_elt( self ):
        return self._selected_elt

    def get_selected_elts( self ):
        return filter(None, [self.get_current_elt()])  # [] if no selection

    def is_in_multi_selection_mode( self ):
        return False  # todo

    def set_current_row( self, row ):
        if row is not None:
            idx = self._model.createIndex(row, 0)
            self.setCurrentIndex(idx)
            self.scrollTo(idx)

    def set_current_key( self, key, select_first=False, accept_near=False ):
        if accept_near:
            row = self._find_nearest_key(key)
        else:
            row = self.model().key2row(key)
            if row is None and select_first and self.list_obj.get_fetched_elements():
                row = 0
        if row is None:
            return False
        self.set_current_row(row)
        return True

    def _find_nearest_key( self, key ):
        for idx, element in enumerate(self.list_obj.get_fetched_elements()):
            if element.key >= key:
                return idx
        if self.list_obj.get_fetched_elements():
            return 0
        else:
            return None  # has no rows

    def selected_keys( self ):
        return None

    def set_object( self, list_obj ):
        self.list_obj = list_obj
        self.model().set_object(list_obj)
        self.resizeColumnsToContents()
        self.list_obj.subscribe(self)

    def keyPressEvent( self, evt ):
        if key_match_any(evt, ['Tab', 'Backtab', 'Ctrl+Tab', 'Ctrl+Shift+Backtab']):
            evt.ignore()  # let splitter or tab view handle it
            return
        QtGui.QTableView.keyPressEvent(self, evt)

    def vscrollValueChanged( self, value ):
        self.check_if_elements_must_be_fetched()

    def resizeEvent( self, evt ):
        result = QtGui.QTableView.resizeEvent(self, evt)
        self.check_if_elements_must_be_fetched()
        return result

    def currentChanged( self, idx, prev_idx ):
        QtGui.QTableView.currentChanged(self, idx, prev_idx)
        if idx.row() != -1:
            self._selected_elt = self.list_obj.get_fetched_elements()[idx.row()]
        else:
            self._selected_elt = None
        self._selected_elements_changed()

    def setVisible( self, visible ):
        QtGui.QTableView.setVisible(self, visible)
        if visible:
            self.selected_elements_changed(self.get_selected_elts())

    def get_last_visible_row( self ):
        first_visible_row = self.verticalHeader().visualIndexAt(0)
        row_height = self.verticalHeader().defaultSectionSize()
        visible_row_count = self.viewport().height() / row_height
        return max(first_visible_row, 0) + visible_row_count + 1

    def check_if_elements_must_be_fetched( self ):
        last_visible_row = self.get_last_visible_row()
        want_element_count = last_visible_row + 1
        force_load = self.want_current_key is not None
        self.list_obj.need_elements_count(last_visible_row + 1, force_load)

    def _on_activated( self, index ):
        elt = self.list_obj.get_fetched_elements()[index.row()]
        for cmd in elt.commands:
            if cmd.id == 'open':
                cmd.run(self, elt.key)
                return

    def _selected_elements_changed( self ):
        self._update_selected_actions()
        if self.isVisible():  # we may being destructed now
            self.selected_elements_changed([self.get_current_elt()])

    def _update_selected_actions( self ):
        # remove previous actions
        action_widget = self
        for action in self._elt_actions:
            action_widget.removeAction(action)
        self._elt_actions = []
        # pick selection and commands
        elt = self.get_current_elt()
        if not elt: return
        element_key = elt.key
        commands = elt.commands
        # create actions
        for cmd in commands:
            action = cmd.make_action(action_widget, self, element_key)
            action.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
            action_widget.addAction(action)
            self._elt_actions.append(action)

    def __del__( self ):
        print '~list_view.View'


view_registry.register_view('list', Handle.from_resp)
