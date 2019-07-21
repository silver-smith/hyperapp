import os
import logging
from ..common.visual_rep import pprint
from ..common.url import UrlWithRoutes
from ..common import dict_coders, cdr_coders
from .commander import Commander
from .command import command
from .services import Services
from .async_application import AsyncApplication

log = logging.getLogger(__name__)


class Application(AsyncApplication, Commander):

    def __init__(self, sys_argv):
        AsyncApplication.__init__(self, sys_argv)
        Commander.__init__(self, commands_kind='view')
        self.services = Services(self.event_loop)
        self._layout_manager = self.services.layout_manager
        self._module_command_registry = self.services.module_command_registry
        self._remoting = self.services.remoting
        self._resource_resolver = self.services.resource_resolver
        self._view_registry = self.services.view_registry
        self._windows = []
        self._state_storage = self.services.application_state_storage

    def get_state(self):
        return [view.get_state() for view in self._windows]

    async def open_windows(self, state):
        for s in state or []:
            await self._window_from_state(s, self, self._module_command_registry, self._view_registry, self._resource_resolver)

    def pick_arg(self, kind):
        return None

    def get_global_commands(self):
        return self._commands

    def window_created(self, view):
        self._windows.append(view)

    def window_closed(self, view):
        state = self.get_state()
        self._windows.remove(view)
        if not self._windows:  # Was it the last window? Then it is time to exit
            self._state_storage.save_state(state)
            self.stop_loop()

    @command('quit')
    def quit(self):
        ## module.set_shutdown_flag()
        state = self.get_state()
        self._state_storage.save_state(state)
        self.stop_loop()

    def exec_(self):
        self.event_loop.run_until_complete(self.services.async_init())
        self._layout_manager.build_default_layout(self)
        AsyncApplication.exec_(self)
