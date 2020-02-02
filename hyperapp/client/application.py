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
        self._async_ref_resolver = self.services.async_ref_resolver
        self._layout_manager = self.services.layout_manager
        self._default_state_builder = self.services.default_state_builder
        self._module_command_registry = self.services.module_command_registry
        self._remoting = self.services.remoting
        self._resource_resolver = self.services.resource_resolver
        # self._view_registry = self.services.view_registry
        self._windows = []
        self._state_storage = self.services.application_state_storage

    async def _async_init(self):
        await self.services.async_init()
        app_state = self._state_storage.load_state()
        if app_state:
            root_view_state = await self._async_ref_resolver.resolve_ref_to_object(app_state.root_layout_ref)
        else:
            root_view_state = self._default_state_builder()
        await self._layout_manager.create_layout_views(root_view_state)

    def run_event_loop(self):
        self.event_loop.run_until_complete(self._async_init())
        AsyncApplication.run_event_loop(self)
        self._save_state()

    def get_current_state(self):
        root_layout_ref = self._layout_manager.root_layout.get_view_ref()
        return self._state_storage.state_t(
            root_layout_ref=root_layout_ref,
            )

    # async def open_windows(self, state):
    #     for s in state or []:
    #         await self._window_from_state(s, self, self._module_command_registry, self._view_registry, self._resource_resolver)

    def pick_arg(self, kind):
        return None

    def get_global_commands(self):
        return self._commands

    # def stop(self):
    #     # self._state_storage.save_state(state)
    #     self.stop_loop()

    # @command('quit')
    # def quit(self):
    #     ## module.set_shutdown_flag()
    #     state = self.get_state()
    #     self._state_storage.save_state(state)
    #     self.stop_loop()

    def _save_state(self):
        state = self.get_current_state()
        self._state_storage.save_state(state)
