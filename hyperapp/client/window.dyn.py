import logging
import weakref
from PySide2 import QtCore, QtWidgets

from hyperapp.common.util import is_list_inst
from hyperapp.client.util import DEBUG_FOCUS, call_after
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from . import htypes
from .view import View
from .tab_view import TabView

log = logging.getLogger(__name__)

LOCALE = 'en'

DEFAULT_SIZE = QtCore.QSize(800, 800)
DUP_OFFSET = QtCore.QPoint(150, 50)


class Window(View, QtWidgets.QMainWindow):

    def __init__(self, on_closed, size=None, pos=None):
        QtWidgets.QMainWindow.__init__(self)
        View.__init__(self)
        self._on_closed = on_closed
        self._child_widget = None
        if size:
            self.resize(size)
        else:
            self.resize(DEFAULT_SIZE)
        if pos:
            self.move(pos)
        else:
            self.move(800, 100)
        #self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._filter_pane)

    def closeEvent(self, evt):
        QtWidgets.QMainWindow.closeEvent(self, evt)
        ## self.deleteLater()  # seems not required, at least when moved to QMainWindow from QWidget
        self._on_closed()

    def get_state(self):
        return htypes.window.window_state(
            tab_view=self._view.get_state(),
            size=htypes.window.size(w=self.width(), h=self.height()),
            pos=htypes.window.pos(x=self.x(), y=self.y()),
            )

    def get_current_child(self):
        return self._view

    ## def replace_view(self, mapper):
    ##     handle = mapper(self._view.handle())
    ##     if handle:
    ##         self.set_child(handle)

    def set_child(self, child):
        self._view = child
        child.set_parent(self)
        self.view_changed(self._view)

    def open(self, handle):
        self._view.open(handle)

    def object_selected(self, obj):
        return False

    def view_changed(self, view):
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

    def view_commands_changed(self, command_kinds):
        self._menu_bar.view_commands_changed(self, command_kinds)
        self._cmd_pane.view_commands_changed(self, command_kinds)
        
    @command('duplicate_window')
    async def duplicate_window(self):
        state = self.get_state()
        state.pos.x += DUP_OFFSET.x()
        state.pos.y += DUP_OFFSET.y()
        await self.from_state(state, self._app, self._module_command_registry, self._view_registry, self._resource_resolver)

    def __del__(self):
        log.info('~window')


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
