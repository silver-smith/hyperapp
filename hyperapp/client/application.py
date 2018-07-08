import os
import logging
from PySide import QtCore, QtGui
from ..common.url import UrlWithRoutes
from ..common import dict_coders, cdr_coders
from .server import Server
from .command import command
from .proxy_object import execute_get_request
from . import view
from . import window
from .services import Services
from .async_application import AsyncApplication
from .application_state_storage import ApplicationStateStorage
from .default_state import build_default_state

log = logging.getLogger(__name__)


class Application(AsyncApplication, view.View):

    def __init__(self, sys_argv):
        AsyncApplication.__init__(self, sys_argv)
        view.View.__init__(self)
        self.services = Services(self.event_loop)
        self._packet_types = self.services.types.packet
        self._module_registry = self.services.module_registry
        self._remoting = self.services.remoting
        self._resources_manager = self.services.resources_manager
        self._view_registry = self.services.view_registry
        self._modules = self.services.modules
        self._windows = []
        self._state_storage = ApplicationStateStorage(
            self.services.types.error,
            self.services.types.module,
            self.services.types.packet,
            self.services.types.resource,
            self.services.types.core,
            self.services.types.param_editor,
            self.services.objimpl_registry,
            self.services.view_registry,
            self.services.param_editor_registry,
            self.services.type_module_repository,
            self.services.resources_manager,
            self.services.module_manager,
            #self.services.code_repository,
            )

    def get_state(self):
        return [view.get_state() for view in self._windows]

    async def open_windows(self, state):
        for s in state or []:
            await window.Window.from_state(s, self, self._module_registry, self._view_registry, self._resources_manager)

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

    @command('open_server')
    async def open_server(self):
        window = self._windows[0]  # usually first window is the current one
        fpath, ftype = QtGui.QFileDialog.getOpenFileName(
            window.get_widget(), 'Load url', os.getcwd(), 'Server url with routes (*.url)')
        url = UrlWithRoutes.load_from_file(self._iface_registry, fpath)
        self._remoting.add_routes_from_url(url)
        server = Server.from_public_key(self._remoting, url.public_key)
        handle = await execute_get_request(self._packet_types, self._remoting, url)
        assert handle  # url's get command must return a handle
        window.get_current_view().open(handle)

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
            state = build_default_state(self._modules)
        self.event_loop.run_until_complete(self.services.async_init())
        self.event_loop.run_until_complete(self.open_windows(state))
        AsyncApplication.exec_(self)
