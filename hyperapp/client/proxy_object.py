import weakref
import uuid
from ..common.util import path2str, str2path
from ..common.interface import Interface, Field, tString, tPath, resolve_iface, iface_registry
from ..common.request import ClientNotification, Request
from .util import make_url
from .object import Object
from .command import Command
from .proxy_registry import proxy_class_registry, proxy_registry
from .server import RespHandler, Server
from . import view


class ObjRespHandler(RespHandler):

    def __init__( self, object, command_id, initiator_view=None ):
        assert isinstance(object, Object), repr(object)
        RespHandler.__init__(self, object.iface, command_id)
        assert initiator_view is None or isinstance(initiator_view, view.View), repr(initiator_view)
        self.object = weakref.ref(object)
        self.initiator_view = weakref.ref(initiator_view) if initiator_view else None  # may be initiated not by a view

    def process_response( self, server, response ):
        object = self.object()
        initiator_view = self.initiator_view() if self.initiator_view else None
        if object:
            object.process_response(server, response, self, initiator_view)


class ProxyObject(Object):

    @staticmethod
    def resolve_persistent_id( persistent_id ):
        objimpl_id, iface_id, server_locator, path_str = persistent_id.split(' ', 3)
        server = Server.resolve_locator(server_locator)
        path = str2path(path_str)
        iface = iface_registry.resolve(iface_id)
        proxy_cls = proxy_class_registry.resolve(objimpl_id)
        return proxy_cls.produce_obj(server, path, iface)

    @classmethod
    def produce_obj_by_objinfo( cls, server, objinfo ):
        object = cls.produce_obj(server, objinfo.path, objinfo.iface)
        object.set_contents(objinfo.contents)
        return object

    # we avoid making proxy objects with same server+path
    @classmethod
    def produce_obj( cls, server, path, iface ):
        object = proxy_registry.resolve(server, path)
        if object is not None:
            print '> proxy object is resolved from registry:', object
            return object
        object = cls(server, path, iface)
        proxy_registry.register(server, path, object)
        print '< proxy object is registered in registry:', object
        return object

    def __init__( self, server, path, iface ):
        Object.__init__(self)
        self.init_flag = None
        self.server = server
        self.path = path
        self.iface = iface
        self.commands = []
        self.resp_handlers = set()  # explicit refs to ObjRespHandlers to keep them alive until object is alive

    def get_module_ids( self ):
        return self.iface.get_module_ids()

    def get_persistent_id( self ):
        return ' '.join([self.get_objimpl_id(),
                         self.iface.iface_id,
                         self.server.get_locator(),
                         path2str(self.path)])

    @staticmethod
    def get_objimpl_id():
        return 'object'

    def subscribe( self, observer ):
        this_is_first_observer = Object.subscribe(self, observer)
        if this_is_first_observer:
            self.execute_request('subscribe')

    def set_contents( self, contents ):
        self.commands = map(Command.decode, contents.commands)

    def get_title( self ):
        return '/' + '/'.join(self.path)

    def get_commands( self ):
        return self.commands

    def get_url( self ):
        return make_url(self.server, self.path)

    def run_command( self, command_id, initiator_view=None, **kw ):
        self.execute_request(command_id, initiator_view, **kw)

    def observers_gone( self ):
        print '-- observers_gone', self
        self.send_notification('unsubscribe')

    # prepare request which does not require/expect response
    def prepare_notification( self, command_id, *args, **kw ):
        params = self.iface.make_params(command_id, *args, **kw)
        return ClientNotification(self.server, self.iface, self.path, command_id, params=params)

    def prepare_request( self, command_id, *args, **kw ):
        request_id = str(uuid.uuid4())
        params = self.iface.make_params(command_id, *args, **kw)
        return Request(self.server, self.iface, self.path, command_id, request_id, params=params)

    def send_notification( self, command_id, *args, **kw ):
        request = self.prepare_notification(command_id, *args, **kw)
        self.server.send_notification(request)

    def execute_request( self, command_id, initiator_view=None, *args, **kw ):
        request = self.prepare_request(command_id, *args, **kw)
        resp_handler = ObjRespHandler(self, command_id, initiator_view)
        self.resp_handlers.add(resp_handler)
        self.server.execute_request(request, resp_handler)

    def process_response( self, server, response, resp_handler, initiator_view=None ):
        self.process_response_result(resp_handler.command_id, response.result)
        self.resp_handlers.remove(resp_handler)
        # initiator_view may already be gone (closed, navigated away) or be missing at all - so is None
        if self.iface.is_open_command(resp_handler.command_id) and initiator_view:
            initiator_view.process_handle_open(server, response.result)

    def process_response_result( self, command_id, result ):
        if command_id == 'subscribe':
            self.process_subscribe_response(result)

    def process_subscribe_response( self, result ):
        self.set_contents(result)
        self._notify_object_changed()

    def process_update( self, diff ):
        raise NotImplementedError(self.__class__)

    def __del__( self ):
        print '~ProxyObject', self, self.path


proxy_class_registry.register(ProxyObject)
