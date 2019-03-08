import os
import logging
from ..common.url import UrlWithRoutes
from ..common import dict_coders, cdr_coders
from .commander import Commander
from .command import command
from .services import Services
from .async_application import AsyncApplication
from .application_state_storage import ApplicationStateStorage

log = logging.getLogger(__name__)


class Application(AsyncApplication, Commander):

    def __init__(self, sys_argv):
        AsyncApplication.__init__(self, sys_argv)
        Commander.__init__(self, commands_kind='view')
        self.services = Services(self.event_loop)
        self._module_command_registry = self.services.module_command_registry
        self._remoting = self.services.remoting
        self._resource_resolver = self.services.resource_resolver
        self._view_registry = self.services.view_registry
        self._window_from_state = self.services.window_from_state
        self._windows = []
#        self._state_storage = ApplicationStateStorage(
#            self.services.types.error,
#            self.services.types.module,
#            self.services.types.packet,
#            self.services.types.resource,
#            self.services.types.core,
#            self.services.types.param_editor,
#            self.services.objimpl_registry,
#            self.services.view_registry,
#            self.services.type_module_repository,
#            self.services.resource_resolver,
#            self.services.module_manager,
#            #self.services.code_repository,
#            )

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
            #self._state_storage.save_state(state)
            self.stop_loop()

    @command('quit')
    def quit(self):
        ## module.set_shutdown_flag()
        state = self.get_state()
        #self._state_storage.save_state(state)
        self.stop_loop()

    def exec_(self):
        #state = self._state_storage.load_state_with_requirements(self.event_loop)
        state = None
        if not state:
            state = self.services.build_default_state()
        self.event_loop.run_until_complete(self.services.async_init())
        self.event_loop.run_until_complete(self.open_windows(state))
        AsyncApplication.exec_(self)
