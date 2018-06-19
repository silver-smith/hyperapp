import logging
import asyncio

from hyperapp.common.interface import hyper_ref as href_types
from hyperapp.common.interface import tcp_transport as tcp_transport_types
from hyperapp.common.tcp_packet import has_full_tcp_packet, encode_tcp_packet, decode_tcp_packet
from ..module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.tcp'
TCP_PACKET_ENCODING = 'cdr'


class TcpProtocol(asyncio.Protocol):

    def __init__(self, event_loop, ref_registry, endpoint_registry, ref_collector_factory, address):
        self._ref_registry = ref_registry
        self._endpoint_registry = endpoint_registry
        self._ref_collector_factory = ref_collector_factory
        self._address = address
        self._recv_buf = b''

    def connection_made(self, asyncio_transport):
        log.info('tcp connection made')
        self._asyncio_transport = asyncio_transport

    def data_received(self, data):
        self._log('%d bytes is received' % len(data))
        self._recv_buf += data
        while has_full_tcp_packet(self._recv_buf):
            packet_data, packet_size = decode_tcp_packet(self._recv_buf)
            transport_packet = decode_transport_packet(packet_data)
            asyncio.async(self._remoting.process_packet(self, self.session_list, self._server_public_key, transport_packet))
            assert packet_size <= len(self._recv_buf), repr(packet_size)
            self._recv_buf = self._recv_buf[packet_size:]
            self._log('consumed %d bytes, remained %d' % (packet_size, len(self._recv_buf)))

    def send(self, message_ref):
        assert isinstance(message_ref, href_types.ref), repr(message_ref)
        ref_collector = self._ref_collector_factory()
        peer_endpoints_ref = self._make_peer_endpoints_ref()
        bundle = ref_collector.make_bundle([peer_endpoints_ref, message_ref])
        data = encode_tcp_packet(bundle, TCP_PACKET_ENCODING)
        self._log('sending data, size=%d' % len(data))
        self._asyncio_transport.write(data)

    def _make_peer_endpoints_ref(self):
        endpoint_ref_list = self._endpoint_registry.get_endpoint_ref_list()
        peer_endpoints = tcp_transport_types.peer_endpoints(endpoint_ref_list=endpoint_ref_list)
        return self._ref_registry.register_object(tcp_transport_types.peer_endpoints, peer_endpoints)

    def _log(self, message):
        log.info('tcp to %s:%d: %s', self._address.host, self._address.port, message)
        

class TcpTransport(object):

    def __init__(self, event_loop):
        self._event_loop = event_loop


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        self._event_loop = services.event_loop
        self._address_to_protocol = {}  # tcp_transport_types.address -> TcpProtocol
        services.transport_registry.register(
            tcp_transport_types.address,
            self._resolve_address,
            services.ref_registry,
            services.endpoint_registry,
            services.ref_collector_factory,
            )

    async def _resolve_address(self, address, ref_registry, endpoint_registry, ref_collector_factory):
        protocol = self._address_to_protocol.get(address)
        if protocol:
            return protocol
        constructor = lambda: TcpProtocol(self._event_loop, ref_registry, endpoint_registry, ref_collector_factory, address)
        asyncio_transport, protocol = await self._event_loop.create_connection(constructor, address.host, address.port)
        self._address_to_protocol[address] = protocol
        return protocol
