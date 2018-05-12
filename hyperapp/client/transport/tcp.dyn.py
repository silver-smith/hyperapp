import logging
import asyncio

from hyperapp.common.interface import tcp_transport as tcp_transport_types
from ..module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.tcp'


class TcpProtocol(asyncio.Protocol):

    def __init__(self, event_loop, address):
        self._address = address
        self._recv_buf = b''

    def connection_made(self, transport):
        log.info('tcp connection made')
        self.transport = transport

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

    def send_packet(self, packet):
        assert isinstance(packet, tTransportPacket), repr(packet)
        contents = encode_transport_packet(packet)
        data = encode_tcp_packet(contents)
        self._log('sending data, size=%d' % len(data))
        self.transport.write(data)

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
        services.transport_registry.register(tcp_transport_types.address, self._resolve_address)

    async def _resolve_address(self, address):
        protocol = self._address_to_protocol.get(address)
        if protocol:
            return protocol
        constructor = lambda: cls(self._event_loop, address)
        transport, protocol = await self._event_loop.create_connection(constructor, address.host, address.port)
        self._address_to_protocol[address] = protocol
        return protocol
