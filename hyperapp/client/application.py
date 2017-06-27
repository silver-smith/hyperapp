import logging
import asyncio
from PySide import QtCore, QtGui
from ..common.url import UrlWithRoutes
from .server import Server
from .command import command
from .proxy_object import execute_get_request
from . import view
from . import window
from .services import Services
from .application_state_storage import ApplicationStateStorage
from .default_state import build_default_state

log = logging.getLogger(__name__)


class Application(QtGui.QApplication, view.View):

    def __init__(self, sys_argv):
        QtGui.QApplication.__init__(self, sys_argv)
        view.View.__init__(self)
        self.services = Services()
        self._iface_registry = self.services.iface_registry
        self._remoting = self.services.remoting
        self._resources_manager = self.services.resources_manager
        self._view_registry = self.services.view_registry
        self._modules = self.services.modules
        self._windows = []
        self._state_storage = ApplicationStateStorage(
            self.services.types.packet,
            self.services.types.resource,
            self.services.types.core,
            self.services.types.param_editor,
            self.services.objimpl_registry,
            self.services.view_registry,
            self.services.type_module_repository,
            self.services.resources_manager,
            self.services.module_manager,
            self.services.code_repository,
            )
        self._loop = asyncio.get_event_loop()
        self._loop.set_debug(True)

    ## @property
    ## def response_mgr(self):
    ##     if not self._constructed: return None
    ##     return self._response_mgr

    def get_state(self):
        return [view.get_state() for view in self._windows]

    @asyncio.coroutine
    def open_windows(self, state):
        for s in state or []:
            yield from window.Window.from_state(s, self, self._view_registry, self._resources_manager)

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
            asyncio.async(self.stop_loop())  # call it async to allow all pending tasks to complete

    @asyncio.coroutine
    def stop_loop(self):
        self._loop.stop()

    @command('open_server')
    @asyncio.coroutine
    def open_server(self):
        window = self._windows[0]  # usually first window is the current one
        fpath, ftype = QtGui.QFileDialog.getOpenFileName(
            window.get_widget(), 'Load url', os.getcwd(), 'Server url with routes (*.url)')
        url = UrlWithRoutes.load_from_file(self._iface_registry, fpath)
        self._remoting.add_routes_from_url(url)
        server = Server.from_public_key(self._remoting, url.public_key)
        handle = yield from execute_get_request(self._remoting, url)
        assert handle  # url's get command must return a handle
        window.get_current_view().open(handle)

    @command('quit')
    def quit(self):
        ## module.set_shutdown_flag()
        state = self.get_state()
        self._state_storage.save_state(state)
        self._loop.stop()

    ## def load_state_and_modules(self):
    ##     state = self.load_state_file()
    ##     if not state:
    ##         return state
    ##     module_ids, modules, pickled_handles = state
    ##     for module in modules:
    ##         self._module_manager.load_code_module(module)
    ##         print '-- module is loaded from state: %r (satisfies %s)' % (module.id, module.satisfies)
    ##     for module in self._module_manager.resolve_ids(module_ids):
    ##         print 'loading cached module required for state: %r' % module.id
    ##         load_client_module(module)
    ##     return pickler.loads(pickled_handles)

    def process_events_and_repeat(self):
        while self.hasPendingEvents():
            self.processEvents()
            # although this event is documented as deprecated, it is essential for qt objects being destroyed:
            self.processEvents(QtCore.QEventLoop.DeferredDeletion)
        self.sendPostedEvents(None, 0)
        self._loop.call_later(0.01, self.process_events_and_repeat)

    def exec_(self):
        state = self._state_storage.load_state_with_requirements(self._loop)
        if not state:
            state = build_default_state(self._modules)
        self._loop.run_until_complete(self.open_windows(state))
        self._loop.call_soon(self.process_events_and_repeat)
        try:
            self._loop.run_forever()
        finally:
            self._loop.close()
