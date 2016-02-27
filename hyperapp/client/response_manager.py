# manage packats - responses and notifications from servers

from ..common.htypes import iface_registry
from ..common.endpoint import Endpoint
from ..common.packet import tPacket
from ..common.visual_rep import pprint
from .request import Request, ResponseBase, Response
from .route_repository import RouteRepository
from .module_manager import ModuleManager
from .code_repository import CodeRepositoryProxy
from .objimpl_registry import objimpl_registry
from .proxy_registry import proxy_registry
from .view_registry import view_registry
from .server import Server


class ResponseManager(object):

    def __init__( self, route_repo, module_mgr, code_repository ):
        assert isinstance(route_repo, RouteRepository), repr(route_repo)
        assert isinstance(module_mgr, ModuleManager), repr(module_mgr)
        assert isinstance(code_repository, CodeRepositoryProxy), repr(code_repository)
        self._route_repo = route_repo
        self._module_mgr = module_mgr
        self._code_repository = code_repository
        self._pending_requests = {}  # (server id, request id) -> Request

    def register_request( self, request_id, request ):
        assert isinstance(request, Request), repr(request)
        assert request_id not in self._pending_requests, repr(request_id)
        self._pending_requests[request_id] = request

    def process_packet( self, server_public_key, packet, payload_decoder ):
        print 'from %s:' % server_public_key.get_short_id_hex()
        pprint(tPacket, packet)
        self._module_mgr.add_modules(packet.aux_info.modules)
        unfulfilled_requirements = filter(self._is_unfulfilled_requirement, packet.aux_info.requirements)
        if unfulfilled_requirements:
            self._code_repository.get_required_modules_and_continue(
                unfulfilled_requirements,
                lambda modules: self._add_modules_and_reprocess_packet(server_public_key, packet, payload_decoder, modules))
        else:
            self._process_packet(server_public_key, packet, payload_decoder)

    def _add_modules_and_reprocess_packet( self, server_public_key, packet, payload_decoder, modules ):
        self._module_mgr.add_modules(modules)
        print 'reprocessing %r from %s' % (packet, server_public_key.get_short_id_hex())
        self._process_packet(server_public_key, packet, payload_decoder)

    def _process_packet( self, server_public_key, packet, payload_decoder ):
        payload = payload_decoder(packet.payload)
        response_or_notification = ResponseBase.from_data(self, iface_registry, payload)
        self._process_updates(response_or_notification.updates)
        if isinstance(response_or_notification, Response):
            response = response_or_notification
            print '   response for request', response.command_id, response.request_id
            request = self._pending_requests.get(response.request_id)
            if not request:
                print 'Received response #%s for a missing (already destroyed) object, ignoring' % response.request_id
                return
            del self._pending_requests[response.request_id]
            server = Server.produce(self._load_endpoint(server_public_key))
            request.process_response(server, response)

    def _process_updates( self, updates ):
        for update in updates:
            obj = proxy_registry.resolve(self, update.path)
            if obj:
                obj.process_update(update.diff)
            # otherwize object is already gone and updates must be discarded

    def _is_unfulfilled_requirement( self, requirement ):
        registry, key = requirement
        if registry == 'object':
            return not objimpl_registry.is_registered(key)
        if registry == 'handle':
            return not view_registry.is_view_registered(key)
        if registry == 'interface':
            return not iface_registry.is_registered(key)
        assert False, repr(registry)  # Unknown registry

    def _load_endpoint( self, server_public_key ):
        routes = self._route_repo.get_routes(server_public_key)
        return Endpoint(server_public_key, routes)
