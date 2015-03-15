import sys
from PySide import QtCore, QtGui

sys.path.append('..')

from util import uni2str, key_match, key_match_any
from object import ObjectObserver
import view_registry
import view


ROW_HEIGHT_PADDING = 3  # same as default QTreeView padding


class Handle(view.Handle):

    @classmethod
    def from_resp( cls, obj, resp ):
        selected_key = resp.get('selected_key')
        return cls(obj, key=selected_key)

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

    def __init__( self, list_obj, visible_columns ):
        QtCore.QAbstractTableModel.__init__(self)
        self.list_obj = list_obj
        self.visible_columns = visible_columns

    def element_count( self ):
        return self.list_obj.element_count()

    def elements_added( self, added_count ):
        element_count = self.list_obj.element_count()
        self.rowsInserted.emit(QtCore.QModelIndex(), element_count - added_count, element_count - 1)

    def data( self, index, role ):
        if role == QtCore.Qt.DisplayRole:
            element = self.list_obj.get_fetched_elements()[index.row()]
            column = self.visible_columns[index.column()]
            return column.type.to_string(element.row[column.idx])
        return None

    def headerData( self, section, orient, role ):
        if role == QtCore.Qt.DisplayRole and orient == QtCore.Qt.Orientation.Horizontal:
            return self.visible_columns[section].title
        hdata = QtCore.QAbstractTableModel.headerData(self, section, orient, role)
        return hdata

    def rowCount( self, parent ):
        if parent == QtCore.QModelIndex() and self.list_obj:
            return self.list_obj.element_count()
        else:
            return 0

    def columnCount( self, parent ):
        if parent == QtCore.QModelIndex() and self.list_obj:
            return len(self.visible_columns)
        else:
            return 0

    def __del__( self ):
        print '~list_view.Model'


class View(view.View, QtGui.QTableView, ObjectObserver):

    def __init__( self, parent, obj, key, selected_keys, select_first ):
        QtGui.QTableView.__init__(self)
        view.View.__init__(self, parent)
        self._select_first = select_first
        self.columns = None
        self.list_obj = None
        self._model = Model(list_obj=None, visible_columns=None)
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
        self.set_object(obj)
        self.set_current_key(key, select_first)

    def handle( self ):
        return Handle(self.get_object(), self.get_current_key(), self.selected_keys(), self._select_first)

    def get_title( self ):
        if self.list_obj:
            return self.list_obj.get_title()

    def get_object( self ):
        return self.list_obj

    def object_changed( self ):
        old_key = self._selected_elt.key
        self.model().layoutChanged.emit()
        self.reset()  # selection etc must be cleared
        # find next or any nearby row
        row = None
        for row, element in enumerate(self.list_obj.get_fetched_elements()):
            if element.key >= old_key:
                break  # use this row
        # else: just use last row
        if row is not None:
            self.set_current_row(row)

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

    def set_current_key( self, key, select_first=False ):
        if select_first:
            row = 0
        else:
            row = None
        for idx, element in enumerate(self.list_obj.get_fetched_elements()):
            if element.key == key:
                row = idx
                break
        if row is not None and row < self.list_obj.element_count():
            self.set_current_row(row)

    def selected_keys( self ):
        return None

    def set_object( self, list_obj ):
        self.model().beginResetModel()
        self.list_obj = list_obj
        self.columns = list_obj.get_columns()
        visible_columns = filter(lambda column: column.title is not None, self.columns)
        self._model.list_obj = self.list_obj
        self._model.visible_columns = visible_columns
        self.model().endResetModel()
        self.resizeColumnsToContents()
        self.list_obj.subscribe(self)

    def keyPressEvent( self, evt ):
        if key_match_any(evt, ['Tab', 'Backtab', 'Ctrl+Tab', 'Ctrl+Shift+Backtab']):
            evt.ignore()  # let splitter or tab view handle it
            return
        QtGui.QTableView.keyPressEvent(self, evt)

    def vscrollValueChanged( self, value ):
        print 'vscrollValueChanged'
        first_visible_row = value
        last_visible_row = self.verticalHeader().visualIndexAt(self.viewport().height())
        print 'vscrollValueChanged, first_visible_row =', first_visible_row, \
          ', last_visible_row =', last_visible_row, \
          'viewport.height =', self.verticalHeader().logicalIndexAt(self.viewport().height())
        row_height = self.verticalHeader().defaultSectionSize()
        visible_row_count = self.viewport().height() / row_height
        self.ensure_elements(first_visible_row + visible_row_count + 1)

    def resizeEvent( self, evt ):
        result = QtGui.QTableView.resizeEvent(self, evt)
        row_height = self.verticalHeader().defaultSectionSize()
        visible_row_count = self.viewport().height() / row_height
        first_visible_row = self.verticalHeader().visualIndexAt(0)
        ## print 'resizeEvent, first_visible_row =', first_visible_row, ', visible_row_count =', visible_row_count
        self.ensure_elements(max(first_visible_row, 0) + visible_row_count + 1)
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

    def ensure_elements( self, element_count ):
        if self.list_obj.are_all_elements_fetched(): return
        old_element_count = self.list_obj.element_count()
        if element_count <= old_element_count: return
        self.list_obj.load_elements(element_count - old_element_count)
        self._model.elements_added(self.list_obj.element_count() - old_element_count)

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
