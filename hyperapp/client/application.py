import os.path
import logging
import asyncio
import pickle as pickle
from PySide import QtCore, QtGui
from ..common.htypes import TList
from ..common.url import UrlWithRoutes
from ..common.visual_rep import pprint
from ..common.requirements_collector import RequirementsCollector
from ..common.packet_coders import packet_coders
from .server import Server
from .command import command
from .proxy_object import execute_get_request
from . import text_object
from . import view
from . import window
from . import tab_view
from . import text_view
from . import navigator
from .services import Services

log = logging.getLogger(__name__)


STATE_FILE_PATH = os.path.expanduser('~/.hyperapp.state')
LOCALE = 'en'


class Application(QtGui.QApplication, view.View):

    state_type = TList(window.state_type)

    def __init__( self, sys_argv ):
        QtGui.QApplication.__init__(self, sys_argv)
        self._response_mgr = None  # View constructor getattr call response_mgr
        view.View.__init__(self)
        self.services = Services()
        self._windows = []
        self._loop = asyncio.get_event_loop()
        self._loop.set_debug(True)

    @property
    def response_mgr( self ):
        return self._response_mgr

    def get_state( self ):
        return [view.get_state() for view in self._windows]

    @asyncio.coroutine
    def open_windows( self, state ):
        for s in state or []:
            yield from window.Window.from_state(s, self, self.services.view_registry, self.services.resources_registry)

    def pick_arg( self, kind ):
        return None

    def get_global_commands( self ):
        return self._commands

    def window_created( self, view ):
        self._windows.append(view)

    def window_closed( self, view ):
        state = self.get_state()
        self._windows.remove(view)
        if not self._windows:  # Was it the last window? Then it is time to exit
            self.save_state(state)
            asyncio.async(self.stop_loop())  # call it async to allow all pending tasks to complete

    @asyncio.coroutine
    def stop_loop( self ):
        self._loop.stop()

    @command('open_server', 'Open server', 'Load server url from file', 'Alt+O')
    @asyncio.coroutine
    def open_server( self ):
        window = self._windows[0]  # usually first window is the current one
        fpath, ftype = QtGui.QFileDialog.getOpenFileName(
            window.get_widget(), 'Load url', os.getcwd(), 'Server url with routes (*.url)')
        url = UrlWithRoutes.load_from_file(self.services.iface_registry, fpath)
        self.services.remoting.add_routes_from_url(url)
        server = Server.from_public_key(self.services.remoting, url.public_key)
        handle = yield from execute_get_request(self.services.remoting, url)
        assert handle  # url's get command must return a handle
        window.get_current_view().open(handle)

    @command('quit', 'Quit', 'Quit application', 'Alt+Q')
    def quit( self ):
        ## module.set_shutdown_flag()
        state = self.get_state()
        self.save_state(state)
        self._loop.stop()

    def save_state( self, state ):
        requirements = RequirementsCollector().collect(self.state_type, state)
        module_ids = list(self._resolve_requirements(requirements))
        modules = self.services.module_mgr.resolve_ids(module_ids)
        for module in modules:
            log.info('-- module is stored to state: %r %r (satisfies %s)', module.id, module.fpath, module.satisfies)
        state_data = packet_coders.encode('cdr', state, self.state_type)
        contents = (module_ids, modules, state_data)
        with open(STATE_FILE_PATH, 'wb') as f:
            pickle.dump(contents, f)

    def _resolve_requirements( self, requirements ):
        for registry_id, id in requirements:
            log.info('requirement for state: %s %r', registry_id, id)
            if registry_id == 'object':
                registry = self.services.objimpl_registry
            elif registry_id == 'handle':
                registry = self.services.view_registry
            elif registry_id == 'interface':
                continue  # todo
            else:
                assert False, repr(registry_id)  # unknown registry id
            module_id = registry.get_dynamic_module_id(id)
            if module_id is not None:  # None for static module
                log.info('dynamic module %r provides %s %r', module_id, registry_id, id)
                yield module_id
    

    ## def load_state_and_modules( self ):
    ##     state = self.load_state_file()
    ##     if not state:
    ##         return state
    ##     module_ids, modules, pickled_handles = state
    ##     for module in modules:
    ##         self._module_mgr.add_module(module)
    ##         print '-- module is loaded from state: %r (satisfies %s)' % (module.id, module.satisfies)
    ##     for module in self._module_mgr.resolve_ids(module_ids):
    ##         print 'loading cached module required for state: %r' % module.id
    ##         load_client_module(module)
    ##     return pickler.loads(pickled_handles)

    def load_state_file( self ):
        try:
            with open(STATE_FILE_PATH, 'rb') as f:
                return pickle.load(f)
        except (EOFError, IOError, IndexError) as x:
            log.info('Error loading state: %r', x)
            return None

    def get_default_state( self ):
        text_handle = text_view.state_type('text_view', text_object.state_type('text', 'hello'))
        navigator_state = navigator.state_type(
            view_id=navigator.View.view_id,
            history=[navigator.item_type('sample text', text_handle)],
            current_pos=0)
        tabs_state = tab_view.state_type(tabs=[navigator_state], current_tab=0)
        window_state = window.state_type(
            tab_view=tabs_state,
            size=window.size_type(600, 500),
            pos=window.point_type(100, 100))
        return [window_state]

    def process_events_and_repeat( self ):
        while self.hasPendingEvents():
            self.processEvents()
            # although this event is documented as deprecated, it is essential for qt objects being destroyed:
            self.processEvents(QtCore.QEventLoop.DeferredDeletion)
        self.sendPostedEvents(None, 0)
        self._loop.call_later(0.01, self.process_events_and_repeat)

    def exec_( self ):
        contents = self.load_state_file()
        if contents:
            module_ids, modules, state_data = contents
            log.info('-- modules loaded from state: ids=%r, modules=%r', module_ids, [module.fpath for module in modules])
            new_modules = self._loop.run_until_complete(self.services.code_repository.get_modules_by_ids(module_ids))
            if new_modules is not None:  # has code repositories?
                modules = new_modules  # load new versions
            self.services.module_mgr.add_modules(modules)
            state = packet_coders.decode('cdr', state_data, self.state_type)
            log.info('-->8 -- loaded state  ------')
            pprint(self.state_type, state)
            log.info('--- 8<------------------------')
        else:
            state = self.get_default_state()
        self._loop.run_until_complete(self.open_windows(state))
        self._loop.call_soon(self.process_events_and_repeat)
        try:
            self._loop.run_forever()
        finally:
            self._loop.close()
