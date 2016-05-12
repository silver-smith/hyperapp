import os.path
import cPickle as pickle
from PySide import QtCore, QtGui
from hyperapp.common.endpoint import Endpoint
from ..common.util import flatten
from ..common.htypes import TList, get_iface, iface_registry
from ..common.visual_rep import pprint
from ..common.packet_coders import packet_coders
from .request import Request
from .server import Server
from .proxy_object import GetRequest
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


STATE_FILE_PATH = os.path.expanduser('~/.hyperapp.state')


class Application(QtGui.QApplication, view.View):

    handles_type = TList(window.data_type)

    def __init__( self, sys_argv ):
        QtGui.QApplication.__init__(self, sys_argv)
        self._response_mgr = None  # View constructor getattr call response_mgr
        view.View.__init__(self)
        self._route_repo = RouteRepository()
        self._module_mgr = ModuleManager()
        self._code_repository = code_repository.get_code_repository()
        self._response_mgr = ResponseManager(self._route_repo, self._module_mgr, self._code_repository)
        self._windows = []

    @property
    def response_mgr( self ):
        return self._response_mgr

    def get_windows_handles( self ):
        return [view.handle() for view in self._windows]

    def open_windows( self, windows_handles ):
        for handle in windows_handles or []:
            handle.construct(self)

    def pick_arg( self, kind ):
        return None

    def get_global_commands( self ):
        return self._commands

    def window_created( self, view ):
        self._windows.append(view)

    def window_closed( self, view ):
        self._windows.remove(view)
        if not self._windows:
            self.save_state([view.handle()])

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
        handles = self.get_windows_handles()
        self.save_state(handles)
        QtGui.QApplication.quit()

    def save_state( self, handles ):
        module_ids = list(flatten(handle.get_module_ids() for handle in handles))
        print 'modules required for state: %s' % module_ids
        modules = self._module_mgr.resolve_ids(module_ids)
        for module in modules:
            print '-- module is stored to state: %r %r (satisfies %s)' % (module.id, module.fpath, module.satisfies)
        handles_data = [h.to_data() for h in handles]
        handles_cdr = packet_coders.encode('cdr', handles_data, self.handles_type)
        state = (module_ids, modules, handles_cdr)
        with file(STATE_FILE_PATH, 'wb') as f:
            pickle.dump(state, f)

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
            with file(STATE_FILE_PATH, 'rb') as f:
                return pickle.load(f)
        except (EOFError, IOError, IndexError) as x:
            print 'Error loading state:', x
            return None

    def get_default_state( self ):
        text_handle = text_view.Handle(text_object.TextObject('hello'))
        window_handle = window.Handle(
            tab_view.Handle([
                navigator.Handle(
                    text_handle)]))
        return [window_handle]

    def _add_modules_and_open_state( self, handles_cdr, modules ):
        self._module_mgr.add_modules(modules)
        handles_data = packet_coders.decode('cdr', handles_cdr, self.handles_type)
        ## print '-->8 -- loaded handles  ------'
        ## pprint(self.handles_type, handles_data)
        ## print '--- 8<------------------------'
        handles = [window.Handle.from_data(rec) for rec in handles_data]
        self.open_windows(handles)

    def exec_( self ):
        state = self.load_state_file()
        if state:
            module_ids, modules, handles_cdr = state
            print '-- modules loaded from state: ids=%r, modules=%r)' % (module_ids, [module.fpath for module in modules])
            self._code_repository.get_modules_by_ids_and_continue(
                module_ids, lambda modules: self._add_modules_and_open_state(handles_cdr, modules))
        else:
            whandles = self.get_default_state()
            self.open_windows(whandles)
            del whandles  # or objects will be kept alive
        QtGui.QApplication.exec_()
