import os.path
import uuid
from PySide import QtCore, QtGui
from ..common.interface import iface_registry
from ..common.request import Request, Response, ServerNotification
from .util import flatten
from .pickler import pickler
from .server import Server
from .view_command import command
from . import text_object
from . import view
from . import window
from . import tab_view
from . import text_view
from . import navigator
from .proxy_registry import RespHandler, proxy_registry
from .view_registry import view_registry
from .code_repository import CodeRepositoryProxy
from .module_loader import ModuleCache, load_client_module


STATE_FILE_PATH = os.path.expanduser('~/.hyperapp.state')


class OpenRespHandler(RespHandler):

    def __init__( self, iface, command_id, app ):
        RespHandler.__init__(self, iface, command_id)
        self.app = app

    def process_response( self, server, response ):
        self.app.process_open_response(server, response.result, self)


class Application(QtGui.QApplication, view.View):

    def __init__( self, sys_argv ):
        QtGui.QApplication.__init__(self, sys_argv)
        view.View.__init__(self)
        self._module_cache = ModuleCache()
        self.server = Server(('localhost', 8888))
        self._code_repository = CodeRepositoryProxy(self.server)
        self._windows = []
        self._resp_handlers = set()  # explicit refs to OpenRespHandlers to keep them alive until object is alive

    def add_modules( self, modules ):
        for module in modules:
            print '-- loading module %r fpath=%r' % (module.id, module.fpath)
            self._module_cache.add_module(module)
            load_client_module(module)

    def process_packet( self, server, packet ):
        self.add_modules(packet.aux.modules)
        unfilfilled_requirements = filter(self._is_unfulfilled_requirement, packet.aux.requirements)
        print '--- requirements:', packet.aux.requirements, ', unfulfilled:', unfilfilled_requirements
        if unfilfilled_requirements:
            self._code_repository.get_required_modules_and_process_packet(unfilfilled_requirements, packet)
            return
        response = packet.decode_server_packet(server, iface_registry)
        ## pprint(tServerPacket, response)
        if isinstance(response, Response):
            print '   response for request', response.command_id, response.request_id
            proxy_registry.process_received_response(server, response)
        else:
            assert isinstance(response, ServerNotification), repr(response)
            proxy_registry.process_received_notification(server, response)

    def _is_unfulfilled_requirement( self, requirement ):
        registry, key = requirement
        if registry == 'object':
            return not proxy_registry.is_class_registered(key)
        if registry == 'handle':
            return not view_registry.is_view_registered(key)
        assert False, repr(registry)  # Unknown registry

    def get_windows_handles( self ):
        return [view.handle() for view in self._windows]

    def open_windows( self, windows_handles ):
        for handle in windows_handles or []:
            handle.construct(self)

    def pick_arg( self, kind ):
        return None

    def get_global_commands( self ):
        management_iface = iface_registry.resolve('server_management')
        management_cmd = window.OpenCommand(
            'open_server', 'Server', 'Open server global commands', 'Alt+G',
            management_iface, path=['management'])
        return [management_cmd]  + self._commands

    def window_created( self, view ):
        self._windows.append(view)

    def window_closed( self, view ):
        self._windows.remove(view)
        if not self._windows:
            self.save_state([view.handle()])

    def process_open_response( self, server, result, resp_handler ):
        # open in any window
        view = self._windows[0].get_current_view()
        view.process_handle_open(server, result)
        self._resp_handlers.remove(resp_handler)

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
        state = (module_ids, modules, pickler.dumps(handles))
        with file(STATE_FILE_PATH, 'wb') as f:
            f.write(pickler.dumps(state))

    def load_state_and_modules( self ):
        state = self.load_state_file()
        if not state:
            return state
        module_ids, modules, pickled_handles = state
        for module in modules:
            self._module_cache.add_module(module)
        for module in self._module_cache.resolve_ids(module_ids):
            print 'loading cached module required for state: %r' % module.id
            load_client_module(module)
        return pickler.loads(pickled_handles)

    def load_state_file( self ):
        try:
            with file(STATE_FILE_PATH, 'rb') as f:
                return pickler.loads(f.read())
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

    def execute_get_request( self, iface, path ):
        command_id = 'get'
        resp_handler = OpenRespHandler(iface, command_id, self)  # must keep explicit reference to it
        request_id = str(uuid.uuid4())
        request = Request(self.server, iface, path, command_id, request_id)
        self.server.execute_request(request, resp_handler)
        self._resp_handlers.add(resp_handler)

    def exec_( self ):
        whandles = self.load_state_and_modules()
        print 'loaded state: ', whandles
        if not whandles:
            whandles = self.get_default_state()
        self.open_windows(whandles)
        del whandles  # or objects will be kept alive
        QtGui.QApplication.exec_()
