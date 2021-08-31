import logging

from PySide2 import QtCore, QtWidgets

from hyperapp.common.module import Module

from . import htypes
from .view import View
from .command import command
from .command_hub import CommandHub

log = logging.getLogger(__name__)


# DEFAULT_SIZE = QtCore.QSize(800, 800)
DUP_OFFSET = QtCore.QPoint(150, 50)


class RootView(View):

    @classmethod
    async def from_state(cls, state, mosaic, view_registry):
        window_list = []
        for window_state in state.window_list:
            window = await cls.create_window(window_state, mosaic, view_registry)
            window_list.append(window)
            window.show()
        return cls(window_list)

    @staticmethod
    async def create_window(state, mosaic, view_registry):
        command_hub = CommandHub()
        menu_bar = await view_registry.invite(state.menu_bar_ref, command_hub)
        command_pane = await view_registry.invite(state.command_pane_ref, command_hub)
        central_view = await view_registry.invite(state.central_view_ref, command_hub)
        window = Window(mosaic, menu_bar, command_pane, central_view, state.size, state.pos)
        await window._async_init(command_hub)
        return window

    def __init__(self, window_list):
        super().__init__()
        self._window_list = window_list

    @property
    def state(self):
        pass


class Window(View, QtWidgets.QMainWindow):

    def __init__(self, mosaic, menu_bar, command_pane, central_view, size, pos):
        QtWidgets.QMainWindow.__init__(self)
        View.__init__(self)
        self._mosaic = mosaic
        self._command_pane = command_pane
        self._child_widget = None
        self.resize(size.w, size.h)
        self.move(pos.x, pos.y)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, command_pane)
        self.setMenuWidget(menu_bar)
        self.setCentralWidget(central_view.qt_widget)

    async def _async_init(self, command_hub):
        await command_hub.init_get_commands(self.get_current_commands)

    # def closeEvent(self, event):
    #     super().closeEvent(event)
    #     self._on_close()

    @property
    def state(self):
        return htypes.window.window(
            menu_bar_ref=self._mosaic.put(self.menuBar().state),
            command_pane_ref=self._mosaic.put(self._command_pane.state),
            central_view_ref=self._mosaic.put(self.centralWidget().state),
            size=htypes.window.size(w=self.width(), h=self.height()),
            pos=htypes.window.pos(x=self.x(), y=self.y()),
            )

    def get_current_child(self):
        return self._view

    def set_child(self, child):
        self._view = child

    def open(self, handle):
        self._view.open(handle)

    def view_commands_changed(self, command_kinds):
        self._menu_bar.view_commands_changed(self, command_kinds)
        self._command_pane.view_commands_changed(self, command_kinds)

    def get_current_commands(self):
        return self.centralWidget().get_current_commands()

    @command
    async def duplicate_window(self):
        state = self.get_state()
        state.pos.x += DUP_OFFSET.x()
        state.pos.y += DUP_OFFSET.y()
        await self.from_state(state, self._app, self._view_registry)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.view_registry.register_actor(
            htypes.window.state,
            RootView.from_state,
            services.mosaic,
            services.view_registry,
            )
