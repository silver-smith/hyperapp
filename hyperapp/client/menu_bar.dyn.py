import logging
import weakref

from PySide2 import QtCore, QtWidgets

from hyperapp.client.util import make_action, make_async_action
from hyperapp.client.command import Command, WindowCommand
from hyperapp.client.module import ClientModule

from . import htypes
from .view_handler import RootVisualItem, ViewHandler

log = logging.getLogger(__name__)


class MenuBarHandler(ViewHandler):

    def __init__(self, state, path, command_hub, view_opener, ref_registry, resource_resolver):
        self._ref_registry = ref_registry
        self._resource_resolver = resource_resolver
        self._command_hub = command_hub

    def get_view_ref(self):
        return self._ref_registry.register_object(htypes.menu_bar.menu_bar())

    async def create_view(self):
        return MenuBar(self._resource_resolver, self._command_hub)

    async def visual_item(self):
        return RootVisualItem('MenuBar')


class MenuBar(QtWidgets.QMenuBar):

    def __init__(self, resource_resolver, command_hub):
        super().__init__()
        self._resource_resolver = resource_resolver
        self._build()
        self._locale = 'en'
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
        resource = self._resource_resolver.resolve(command.resource_key, self._locale)
        if resource:
            text = resource.text
            shortcut_list = resource.shortcut_list
        else:
            text = '.'.join(command.resource_key.path)
            shortcut_list = None
        if not command.is_enabled():
            shortcut_list = None
        if used_shortcut_set is not None:
            # remove duplicates
            shortcut_list = [sc for sc in shortcut_list or [] if sc not in used_shortcut_set]
            used_shortcut_set |= set(shortcut_list)
        action = make_async_action(menu, text, shortcut_list, command.run)
        action.setEnabled(command.is_enabled())
        return action

    def __del__(self):
        log.info('~menu_bar')


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.view_registry.register_type(
            htypes.menu_bar.menu_bar, MenuBarHandler, services.ref_registry, services.resource_resolver)
