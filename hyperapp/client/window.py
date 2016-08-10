import logging
import asyncio
import weakref
from PySide import QtCore, QtGui
from ..common.util import is_list_inst
from ..common.htypes import tInt, Field, TRecord, Interface
from .util import DEBUG_FOCUS, call_after
from .command import command
from . import view
from . import composite
from .menu_bar import MenuBar
from . import cmd_pane
from . import tab_view

log = logging.getLogger(__name__)


LOCALE = 'en'


DEFAULT_SIZE = QtCore.QSize(800, 800)
DUP_OFFSET = QtCore.QPoint(150, 50)


point_type = TRecord([
    Field('x', tInt),
    Field('y', tInt),
    ])

size_type = TRecord([
    Field('w', tInt),
    Field('h', tInt),
    ])

state_type = TRecord([
    Field('tab_view', tab_view.state_type),
    Field('size', size_type),
    Field('pos', point_type),
    ])


class Window(composite.Composite, QtGui.QMainWindow):

    @classmethod
    @asyncio.coroutine
    def from_state( cls, state, app, view_registry, resources_manager ):
        locale = LOCALE
        child = yield from tab_view.View.from_state(locale, state.tab_view, view_registry)
        return cls(locale, view_registry, resources_manager, app, child,
                   size=QtCore.QSize(state.size.w, state.size.h),
                   pos=QtCore.QPoint(state.pos.x, state.pos.y))

    def __init__( self, locale, view_registry, resources_manager, app, child, size=None, pos=None ):
        assert isinstance(child, tab_view.View), repr(child)
        QtGui.QMainWindow.__init__(self)
        composite.Composite.__init__(self, app)
        self._locale = locale
        self._view_registry = view_registry
        self._resources_manager = resources_manager
        self._app = app  # alias for _parent()
        self._view = None
        self._child_widget = None
        if size:
            self.resize(size)
        else:
            self.resize(DEFAULT_SIZE)
        if pos:
            self.move(pos)
        else:
            self.move(800, 100)
        self._menu_bar = MenuBar(app, weakref.ref(self), LOCALE, resources_manager)
        self._cmd_pane = cmd_pane.View(self, LOCALE, resources_manager)
        #self._filter_pane = filter_pane.View(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._cmd_pane)
        #self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._filter_pane)
        self.set_child(child)
        self.show()
        self._parent().window_created(self)

    def closeEvent( self, evt ):
        QtGui.QMainWindow.closeEvent(self, evt)
        ## self.deleteLater()  # seems not required, at least when moved to QMainWindow from QWidget
        self._parent().window_closed(self)

    def get_state( self ):
        return state_type(
            tab_view=self._view.get_state(),
            size=size_type(w=self.width(), h=self.height()),
            pos=point_type(x=self.x(), y=self.y()),
            )

    def get_current_child( self ):
        return self._view

    ## def replace_view( self, mapper ):
    ##     handle = mapper(self._view.handle())
    ##     if handle:
    ##         self.set_child(handle)

    def set_child( self, child ):
        self._view = child
        child.set_parent(self)
        self.view_changed(self._view)

    def open( self, handle ):
        self._view.open(handle)

    def object_selected( self, obj ):
        return False

    def view_changed( self, view ):
        assert view is self._view
        w = self._view.get_widget()
        if w is not self._child_widget:
            if DEBUG_FOCUS: log.info('*** window.view_changed: replacing widget self=%r view=%r w=%r old-w=%r', self, view, w, self._child_widget)
            if self._child_widget:
                self._child_widget.deleteLater()
            self.setCentralWidget(w)
            self._child_widget = w
        self.setWindowTitle(view.get_title())
        self._menu_bar.view_changed(self)
        self._cmd_pane.view_changed(self)
        #self._filter_pane.view_changed(self)

    def view_commands_changed( self, command_kinds ):
        self._menu_bar.view_commands_changed(self, command_kinds)
        self._cmd_pane.view_commands_changed(self, command_kinds)
        
    @command('duplicate_window')
    @asyncio.coroutine
    def duplicate_window( self ):
        state = self.get_state()
        state.pos.x += DUP_OFFSET.x()
        state.pos.y += DUP_OFFSET.y()
        yield from self.from_state(state, self._app, self._view_registry, self._resources_manager)

    def __del__( self ):
        log.info('~window')
