import logging
import asyncio
import abc
from ..common.util import is_list_inst
from ..common.endpoint import Endpoint
from ..common.transport_packet import tTransportPacket
from ..common.interface.code_repository import tRequirement
from .request import Request, ClientNotification, Response
from .module_manager import ModuleManager
#from .code_repository import CodeRepository

log = logging.getLogger(__name__)


class Transport(metaclass=abc.ABCMeta):

    def __init__( self, module_mgr, code_repository, iface_registry, objimpl_registry, view_registry ):
        assert isinstance(module_mgr, ModuleManager), repr(module_mgr)
        #assert isinstance(code_repository, CodeRepository), repr(code_repository)
        self._module_mgr = module_mgr
        self._code_repository = code_repository
        self._iface_registry = iface_registry
        self._objimpl_registry = objimpl_registry
        self._view_registry = view_registry

    @asyncio.coroutine
    def resolve_requirements( self, requirements ):
        assert is_list_inst(requirements, tRequirement), repr(requirements)
        unfulfilled_requirements = list(filter(self._is_unfulfilled_requirement, requirements))
        if not unfulfilled_requirements: return
        modules = yield from self._code_repository.get_modules_by_requirements(unfulfilled_requirements)
        self._module_mgr.add_modules(modules)
        
    def _is_unfulfilled_requirement( self, requirement ):
        registry, key = requirement
        if registry == 'object':
            return not self._objimpl_registry.is_registered(key)
        if registry == 'handle':
            return not self._view_registry.is_view_registered(key)
        if registry == 'interface':
            return not self._iface_registry.is_registered(key)
        assert False, repr(registry)  # Unknown registry

    @asyncio.coroutine
    @abc.abstractmethod
    def send_request_rec( self, endpoint, route, request_or_notification ):
        pass

    @asyncio.coroutine
    @abc.abstractmethod
    def process_packet( self, protocol, session_list, server_public_key, data ):
        pass


class TransportRegistry(object):

    def __init__( self ):
        self._id2transport = {}
        self._futures = {}  # request id -> future for response

    def register( self, id, transport ):
        assert isinstance(id, str), repr(id)
        assert isinstance(transport, Transport), repr(transport)
        self._id2transport[id] = transport

    def resolve( self, id ):
        return self._id2transport[id]

    @asyncio.coroutine
    def execute_request( self, endpoint, request ):
        assert isinstance(endpoint, Endpoint), repr(endpoint)
        assert isinstance(request, Request), repr(request)
        self._futures[request.request_id] = future = asyncio.Future()
        try:
            yield from self.send_request_or_notification(endpoint, request)
            return (yield from future)
        finally:
            del self._futures[request.request_id]

    @asyncio.coroutine
    def send_notification( self, endpoint, notification ):
        assert isinstance(endpoint, Endpoint), repr(endpoint)
        assert isinstance(notification, ClientNotification), repr(notification)
        yield from self.send_request_or_notification(endpoint, notification)

    @asyncio.coroutine
    def send_request_or_notification( self, endpoint, request_or_notification ):
        for route in endpoint.routes:
            transport_id = route[0]
            transport = self._id2transport.get(transport_id)
            if not transport:
                log.info('Warning: unknown transport: %r', transport_id)
                continue
            try:
                return (yield from transport.send_request_rec(endpoint, route[1:], request_or_notification))
            except:
                # todo: catch specific exceptions; try next route
                raise
        raise RuntimeError('Unable to send packet to %s - no reachable transports'
                           % server.get_endpoint().public_key.get_short_id_hex())

    @asyncio.coroutine
    def process_packet( self, protocol, session_list, server_public_key, packet ):
        assert isinstance(packet, tTransportPacket), repr(packet)
        log.info('received %r packet, contents %d bytes', packet.transport_id, len(packet.data))
        transport = self.resolve(packet.transport_id)
        response_or_notification = yield from transport.process_packet(protocol, session_list, server_public_key, packet.data)
        if isinstance(response_or_notification, Response):
            future = self._futures.get(response_or_notification.request_id)
            if future:
                future.set_result(response_or_notification)
        

transport_registry = TransportRegistry()
