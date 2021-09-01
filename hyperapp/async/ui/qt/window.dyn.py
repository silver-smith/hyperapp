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
    async def from_state(cls, state, mosaic, async_stop_event, view_registry):
        self = cls(mosaic, async_stop_event, view_registry)
        await self._async_init(state.window_list)
        return self

    def __init__(self, mosaic, async_stop_event, view_registry):
        super().__init__()
        self._mosaic = mosaic
        self._async_stop_event = async_stop_event
        self._view_registry = view_registry
        self._window_list = None

    async def _async_init(self, window_state_list):
        self._window_list = []
        for window_state in window_state_list:
            window = await self._create_window(window_state)
            self._window_list.append(window)
            window.show()

    async def _create_window(self, state):
        command_hub = CommandHub()
        menu_bar = await self._view_registry.invite(state.menu_bar_ref, command_hub)
        command_pane = await self._view_registry.invite(state.command_pane_ref, command_hub)
        central_view = await self._view_registry.invite(state.central_view_ref, command_hub)
        window = Window(self._mosaic, self._async_stop_event, self, command_hub, menu_bar, command_pane, central_view, state.size, state.pos)
        await window._async_init()
        return window

    @property
    def state(self):
        return htypes.window.state(
            window_list=[
                window.state for window in self._window_list
                ],
            )

    def iter_view_commands(self):
        for idx, window in enumerate(self._window_list):
            for path, command in window.iter_view_commands():
                yield ([f"window#{idx}", *path], command)

    async def update_commands(self):
        for window in self._window_list:
            await window.update_commands()


class Window(View, QtWidgets.QMainWindow):

    def __init__(self, mosaic, async_stop_event, root_view, command_hub, menu_bar, command_pane, central_view, size, pos):
        QtWidgets.QMainWindow.__init__(self)
        View.__init__(self)
        self._mosaic = mosaic
        self._async_stop_event = async_stop_event
        self._root_view = root_view
        self._command_hub = command_hub
        self._command_pane = command_pane
        self._child_widget = None
        self.resize(size.w, size.h)
        self.move(pos.x, pos.y)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, command_pane)
        self.setMenuWidget(menu_bar)
        self.setCentralWidget(central_view.qt_widget)

    async def _async_init(self):
        await self._command_hub.init_get_commands(self.get_current_commands)

    def closeEvent(self, event):
        super().closeEvent(event)
        if len(self._root_view._window_list) == 1:
            self._async_stop_event.set()
            return  # Do not remove last window from list - we will need to store it to state.
        idx = self._root_view._window_list.index(self)
        del self._root_view._window_list[idx]

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
        return self.centralWidget()

    def view_commands_changed(self, command_kinds):
        self._menu_bar.view_commands_changed(self, command_kinds)
        self._command_pane.view_commands_changed(self, command_kinds)

    def iter_view_commands(self):
        yield from self.centralWidget().iter_view_commands()
        for command in self.get_command_list():
            yield ([], command)

    async def get_current_commands(self):
        return [
            *await self.centralWidget().get_current_commands(),
            *self.get_command_list(),
            ]

    async def update_commands(self):
        await self._command_hub.update()

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
            services.async_stop_event,
            services.view_registry,
            )
