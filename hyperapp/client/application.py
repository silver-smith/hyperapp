import os.path
import logging
import asyncio
import pickle as pickle
from PySide import QtCore, QtGui
from hyperapp.common.endpoint import Endpoint
from ..common.util import flatten
from ..common.htypes import TList, get_iface, iface_registry
from ..common.visual_rep import pprint
from ..common.packet_coders import packet_coders
from .request import Request
from .server import Server
from .view_command import command
from . import text_object
from . import view
from . import window
from . import tab_view
from . import text_view
from . import navigator
from . import window
from .objimpl_registry import objimpl_registry
from . import code_repository
from .module_manager import ModuleManager
from .response_manager import ResponseManager
from .route_repository import RouteRepository

log = logging.getLogger(__name__)


STATE_FILE_PATH = os.path.expanduser('~/.hyperapp.state')


class Application(QtGui.QApplication, view.View):

    state_type = TList(window.state_type)

    def __init__( self, sys_argv ):
        QtGui.QApplication.__init__(self, sys_argv)
        self._response_mgr = None  # View constructor getattr call response_mgr
        view.View.__init__(self)
        self._route_repo = RouteRepository()
        self._module_mgr = ModuleManager()
        self._code_repository = code_repository.get_code_repository()
        self._response_mgr = ResponseManager(self._route_repo, self._module_mgr, self._code_repository)
        self._windows = []
        self._loop = asyncio.get_event_loop()
        self._loop.set_debug(True)

    @property
    def response_mgr( self ):
        return self._response_mgr

    def get_state( self ):
        return [view.get_state() for view in self._windows]

    def open_windows( self, state ):
        for s in state or []:
            window.Window.from_state(self, s)

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

    @command('Open server', 'Load server endpoint from file', 'Alt+O')
    def open_server( self ):
        window = self._windows[0]  # usually first window is the current one
        fpath, ftype = QtGui.QFileDialog.getOpenFileName(
            window.get_widget(), 'Load endpoint', os.getcwd(), 'Server endpoint (*.endpoint)')
        endpoint = Endpoint.load_from_file(fpath)
        server = Server.from_endpoint(endpoint)
        url = server.make_url(iface_registry.resolve('server_management'), ['management'])
        GetRequest(url, window.get_current_view()).execute()

    @command('Quit', 'Quit application', 'Alt+Q')
    def quit( self ):
        ## module.set_shutdown_flag()
        state = self.get_state()
        self.save_state(state)
        self._loop.stop()

    def save_state( self, state ):
        ## module_ids = list(flatten(handle.get_module_ids() for handle in handles))
        ## log.info('modules required for state: %s', module_ids)
        ## modules = self._module_mgr.resolve_ids(module_ids)
        ## for module in modules:
        ##     log.info('-- module is stored to state: %r %r (satisfies %s)', module.id, module.fpath, module.satisfies)
        state_data = packet_coders.encode('cdr', state, self.state_type)
        ## contents = (module_ids, modules, state_data)
        contents = state_data
        with open(STATE_FILE_PATH, 'wb') as f:
            pickle.dump(contents, f)

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
            state_data = contents
            ## module_ids, modules, state_data = contents
            ## log.info('-- modules loaded from state: ids=%r, modules=%r', module_ids, [module.fpath for module in modules])
            ## self._module_mgr.add_modules(modules)
            state = packet_coders.decode('cdr', state_data, self.state_type)
            log.info('-->8 -- loaded state  ------')
            pprint(self.state_type, state)
            log.info('--- 8<------------------------')
            self.open_windows(state)
        else:
            state = self.get_default_state()
            self.open_windows(state)
        self._loop.call_soon(self.process_events_and_repeat)
        try:
            self._loop.run_forever()
        finally:
            self._loop.close()
