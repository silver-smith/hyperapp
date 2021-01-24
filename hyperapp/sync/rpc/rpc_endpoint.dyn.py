from functools import partial

from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module import Module

from . import htypes


class RpcEndpoint:

    def __init__(self, web, types):
        self._types = types
        self._servant_by_id = {}
        self._message_registry = registry = CodeRegistry('rpc_message', web, types)
        registry.register_actor(htypes.rpc.request, self._handle_request)

    def register_servant(self, object_id, servant):
        self._servant_by_id[object_id] = servant

    def process(self, request):
        self._message_registry.invite(request.ref_list[0])

    def _handle_request(self, request):
        servant = self._servant_by_id[request.object_id]
        params = self._types.resolve_ref(request.params_ref).value
        method = getattr(servant, request.method_name)
        result = method(**params._asdict())
        # todo: send response with result or exception


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.rpc_endpoint_factory = partial(RpcEndpoint, services.web, services.types)
