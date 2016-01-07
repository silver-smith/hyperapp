# code repository proxy

from ..common.interface.code_repository import code_repository_iface
from .request import Request
from .server import Server
from .proxy_object import ProxyObject


class GetModulesRequest(Request):

    def __init__( self, iface, path, command_id, params, continuation ):
        Request.__init__(self, iface, path, command_id, params)
        self.continuation = continuation

    def process_response( self, server, response ):
        self.continuation(response.result.modules)


class CodeRepositoryProxy(ProxyObject):

    def __init__( self, server ):
        path = ['code_repository', 'code_repository']
        ProxyObject.__init__(self, server, path, code_repository_iface)

    def get_modules_and_continue( self, module_ids, continuation ):
        command_id = 'get_modules'
        params = self.iface.make_params(command_id, module_ids=module_ids)
        request = GetModulesRequest(self.iface, self.path, command_id, params, continuation)
        self.server.execute_request(request)

    def get_required_modules_and_continue( self, requirements, continuation ):
        command_id = 'get_required_modules'
        params = self.iface.make_params(command_id, requirements=requirements)
        request = GetModulesRequest(self.iface, self.path, command_id, params, continuation)
        self.server.execute_request(request)
