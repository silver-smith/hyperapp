import os.path
import cPickle as pickle
from PySide import QtCore, QtGui
from hyperapp.common.endpoint import Endpoint
from ..common.interface import TList, get_iface, iface_registry
from ..common.visual_rep import pprint
from ..common.packet_coders import packet_coders
from .util import flatten
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
from .view_registry import view_registry
from .code_repository import CodeRepositoryProxy
from .module_loader import ModuleCache, load_client_module
from .get_request import run_get_request


STATE_FILE_PATH = os.path.expanduser('~/.hyperapp.state')


## class OpenRespHandler(RespHandler):

##     def __init__( self, iface, command_id, app ):
##         RespHandler.__init__(self, iface, command_id)
##         self.app = app

##     def process_response( self, response, server ):
##         self.app.process_open_response(response.result, server, self)


class Application(QtGui.QApplication, view.View):

    handles_type = TList(window.data_type)

    def __init__( self, server_endpoint, sys_argv ):
        QtGui.QApplication.__init__(self, sys_argv)
        view.View.__init__(self)
        self._module_cache = ModuleCache()
        self.server = Server.produce(server_endpoint)
        self._code_repository = CodeRepositoryProxy(self.server)
        self._windows = []


    def add_modules( self, modules ):
        for module in modules:
            print '-- loading module %r fpath=%r' % (module.id, module.fpath)
            self._module_cache.add_module(module)
            load_client_module(module)

    def has_unfulfilled_requirements( self, requirements ):
        unfilfilled_requirements = filter(self._is_unfulfilled_requirement, requirements)
        print '-- requirements:', requirements, ', unfulfilled:', unfilfilled_requirements
        return unfilfilled_requirements != []

    def request_required_modules_and_reprocess_packet( self, server, packet ):
        unfilfilled_requirements = filter(self._is_unfulfilled_requirement, packet.aux.requirements)
        assert unfilfilled_requirements
        self._code_repository.get_required_modules_and_continue(
            unfilfilled_requirements, lambda modules: self._add_modules_and_reprocess_packet(server, packet, modules))

    def _add_modules_and_reprocess_packet( self, server, packet, modules ):
        self.add_modules(modules)
        server.reprocess_packet(packet)

    def _is_unfulfilled_requirement( self, requirement ):
        registry, key = requirement
        if registry == 'object':
            return not objimpl_registry.is_registered(key)
        if registry == 'handle':
            return not view_registry.is_view_registered(key)
        if registry == 'interface':
            return not iface_registry.is_registered(key)
        assert False, repr(registry)  # Unknown registry


    def get_windows_handles( self ):
        return [view.handle() for view in self._windows]

    def open_windows( self, windows_handles ):
        for handle in windows_handles or []:
            handle.construct(self)

    def pick_arg( self, kind ):
        return None

    def get_global_commands( self ):
        management_cmd = window.OpenCommand(
            'open_server', 'Server', 'Open server global commands', 'Alt+G', self.server.make_url(['management']))
        return [management_cmd]  + self._commands

    def window_created( self, view ):
        self._windows.append(view)

    def window_closed( self, view ):
        self._windows.remove(view)
        if not self._windows:
            self.save_state([view.handle()])

    @command('Open server', 'Load server endpoint from file', 'Alt+O')
    def open_server( self ):
        # open in any window
        window = self._windows[0]
        fpath, ftype = QtGui.QFileDialog.getOpenFileName(
            window.get_widget(), 'Load endpoint', os.getcwd(), 'Server endpoint (*.endpoint)')
        endpoint = Endpoint.load_from_file(fpath)
        server = Server.produce(endpoint)
        url = server.make_url(['management'])
        run_get_request(window.get_current_view(), url)

    @command('Quit', 'Quit application', 'Alt+Q')
    def quit( self ):
        ## module.set_shutdown_flag()
        handles = self.get_windows_handles()
        self.save_state(handles)
        QtGui.QApplication.quit()

    def save_state( self, handles ):
        module_ids = list(flatten(handle.get_module_ids() for handle in handles))
        print 'modules required for state: %s' % module_ids
        modules = self._module_cache.resolve_ids(module_ids)
        for module in modules:
            print '-- module is stored to state: %r (satisfies %s)' % (module.id, module.satisfies)
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
    ##         self._module_cache.add_module(module)
    ##         print '-- module is loaded from state: %r (satisfies %s)' % (module.id, module.satisfies)
    ##     for module in self._module_cache.resolve_ids(module_ids):
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

    ## def execute_get_request( self, url ):
    ##     server, path = Server.resolve_url(url)
    ##     command_id = 'get'
    ##     resp_handler = OpenRespHandler(get_iface, command_id, self)  # must keep explicit reference to it
    ##     request = Request(get_iface, path, command_id)
    ##     server.execute_request(request, resp_handler)
    ##     self._resp_handlers.add(resp_handler)

    ## def process_open_response( self, result, server, resp_handler ):
    ##     # open in any window
    ##     view = self._windows[0].get_current_view()
    ##     view.process_handle_open(result, server)
    ##     self._resp_handlers.remove(resp_handler)

    def _add_modules_and_open_state( self, handles_cdr, modules ):
        self.add_modules(modules)
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
            self._code_repository.get_modules_and_continue(
                module_ids, lambda modules: self._add_modules_and_open_state(handles_cdr, modules))
        else:
            whandles = self.get_default_state()
            self.open_windows(whandles)
            del whandles  # or objects will be kept alive
        QtGui.QApplication.exec_()
