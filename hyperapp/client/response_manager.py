# manage packats - responses and notifications from servers

from ..common.htypes import iface_registry
from ..common.packet import tPacket
from ..common.visual_rep import pprint
from .request import Request
from .module_manager import ModuleManager
from .code_repository import CodeRepositoryProxy
from .objimpl_registry import objimpl_registry
from .view_registry import view_registry


class RequestRegistry(object):

    def __init__( self ):
        self._pending_requests = {}  # (server id, request id) -> Request

    def register( self, request_id, request ):
        assert isinstance(request, Request), repr(request)
        assert request_id not in self._pending_requests, repr(request_id)
        self._pending_requests[request_id] = request

    def resolve( self, request_id ):
        return self._pending_requests.get(request_id)


class ResponseManager(object):

    def __init__( self, module_mgr, code_repository ):
        assert isinstance(module_mgr, ModuleManager), repr(module_mgr)
        assert isinstance(code_repository, CodeRepositoryProxy), repr(code_repository)
        self._module_mgr = module_mgr
        self._code_repository = code_repository
        self._request_registry = RequestRegistry()

    def register_request( self, request_id, request ):
        self._request_registry.register(request_id, request)

    def process_packet( self, server_public_key, packet ):
        print 'from %s:' % server_public_key.get_short_id_hex()
        pprint(tPacket, packet)
        self._module_mgr.add_modules(packet.aux_info.modules)
        unfulfilled_requirements = filter(self._is_unfulfilled_requirement, packet.aux_info.requirements)
        if unfulfilled_requirements:
            self._code_repository.get_required_modules_and_continue(
                unfulfilled_requirements, lambda modules: self._add_modules_and_reprocess_packet(server_public_key, packet, modules))
        else:
            self._process_packet(server_public_key, packet)

    def _add_modules_and_reprocess_packet( self, server_public_key, packet, modules ):
        self._module_mgr.add_modules(modules)
        print 'reprocessing %r from %s' % (packet, server_public_key.get_short_id_hex())
        self._process_packet(server_public_key, packet)

    def _process_packet( self, server_public_key, packet ):
        assert 0

    def _is_unfulfilled_requirement( self, requirement ):
        registry, key = requirement
        if registry == 'object':
            return not objimpl_registry.is_registered(key)
        if registry == 'handle':
            return not view_registry.is_view_registered(key)
        if registry == 'interface':
            return not iface_registry.is_registered(key)
        assert False, repr(registry)  # Unknown registry
