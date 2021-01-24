from functools import partial

from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module import Module

from . import htypes


class RpcEndpoint:

    def __init__(self, web, types):
        self._message_registry = registry = CodeRegistry('rpc_message', web, types)
        registry.register_actor(htypes.rpc.request, self._handle_request)

    def process(self, request):
        self._message_registry.invite(request.ref_list[0])

    def _handle_request(self, request):
        raise NotImplementedError('todo')


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.rpc_endpoint_factory = partial(RpcEndpoint, services.web, services.types)
