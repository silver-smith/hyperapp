# code repository proxy

from ..common.interface.code_repository import code_repository_iface
from .server import Server
from .proxy_object import ObjRespHandler, ProxyObject


class PacketRespHandler(ObjRespHandler):

    def __init__( self, object, command_id, continuation ):
        ObjRespHandler.__init__(self, object, command_id)
        self.continuation = continuation  # fn(modules)

    def process_response( self, server, response ):
        object = self.object()
        if object:
            object.process_response(server, response, self)


class CodeRepositoryProxy(ProxyObject):

    def __init__( self, server ):
        path = ['code_repository', 'code_repository']
        ProxyObject.__init__(self, server, path, code_repository_iface)

    def get_modules_and_continue( self, module_ids, continuation ):
        command_id = 'get_modules'
        request = self.prepare_request(command_id, module_ids=module_ids)
        resp_handler = PacketRespHandler(self, command_id, continuation)
        self.resp_handlers.add(resp_handler)
        self.server.execute_request(request, resp_handler)

    def get_required_modules_and_continue( self, requirements, continuation ):
        command_id = 'get_required_modules'
        request = self.prepare_request(command_id, requirements=requirements)
        resp_handler = PacketRespHandler(self, command_id, continuation)
        self.resp_handlers.add(resp_handler)
        self.server.execute_request(request, resp_handler)

    def process_response( self, server, response, resp_handler, initiator_view=None ):
        if resp_handler.command_id in ['get_modules', 'get_required_modules']:
            self.process_get_modules_response(resp_handler.continuation, response.result)
        ProxyObject.process_response(self, server, response, resp_handler, initiator_view)

    def process_get_modules_response( self, continuation, result ):
        continuation(result.modules)
