import logging
import asyncio
from ..common.endpoint import Endpoint
from ..common.transport_packet import tTransportPacket
from . request import Request

log = logging.getLogger(__name__)


class Transport(object):

    def send_packet( self, server, route, packet ):
        raise NotImplementedError(self.__class__)


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

    def process_packet( self, connection, session_list, server_public_key, packet ):
        assert isinstance(packet, tTransportPacket), repr(packet)
        log.info('received %r packet, contents %d bytes', packet.transport_id, len(packet.data))
        transport = self.resolve(packet.transport_id)
        transport.process_packet(connection, session_list, server_public_key, packet.data)
        

transport_registry = TransportRegistry()
