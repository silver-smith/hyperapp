import asyncio
import logging
import weakref
from functools import partial

from PySide2 import QtCore, QtWidgets

from . import htypes
from .layout import GlobalLayout
from .module import ClientModule

log = logging.getLogger(__name__)


class MenuBarLayout(GlobalLayout):

    def __init__(self, state, path, command_hub, view_opener, mosaic, plcs):
        super().__init__(path)
        self._mosaic = mosaic
        self._plcs = plcs
        self._command_hub = command_hub

    @property
    def piece(self):
        return htypes.menu_bar.menu_bar()

    async def create_view(self):
        return MenuBar(self._mosaic, self._plcs, self._command_hub)

    async def visual_item(self):
        return self.make_visual_item('MenuBar')


class MenuBar(QtWidgets.QMenuBar):

    def __init__(self, mosaic, plcs, command_hub):
        super().__init__()
        self._mosaic = mosaic
        self._plcs = plcs
        self._build()
        self._locale = 'en'
        self._command_shortcut_d_ref = mosaic.put(htypes.command.command_shortcut_d())
        command_hub.subscribe(self)

    # command hub observer method
    def commands_changed(self, kind, command_list):
        if kind == 'global':
            self._update_menu(self._file_menu, command_list)
        if kind == 'object':
            self._update_menu(self._dir_menu, command_list)
        if kind == 'view':
            self._update_menu(self._view_menu, command_list)

    def _build(self):
        self._file_menu = QtWidgets.QMenu('&File')
        self._dir_menu = QtWidgets.QMenu('&Dir')
        self._view_menu = QtWidgets.QMenu('La&yout')
        self.addMenu(self._file_menu)
        self.addMenu(self._dir_menu)
        self.addMenu(self._view_menu)

    def _update_menu(self, menu, command_list):
        menu.clear()
        for command in command_list:
            menu.addAction(self._make_action(menu, command))

    def _make_action(self, menu, command, used_shortcut_set=None):
        text = command.name
        command_ref = self._mosaic.put(command.piece)
        shortcut = self._plcs.get([command_ref, self._command_shortcut_d_ref])

        if used_shortcut_set is not None:
            # remove duplicates
            if shortcut in used_shortcut_set:
                shortcut = None
            else:
                used_shortcut_set.add(shortcut)

        action = QtWidgets.QAction(text, menu)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(partial(self._run_command, command))
        return action

    def _run_command(self, command):
        asyncio.create_task(command.run())


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.view_registry.register_actor(
            htypes.menu_bar.menu_bar, MenuBarLayout, services.mosaic, services.plcs)
