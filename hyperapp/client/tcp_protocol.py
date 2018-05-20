import logging
import asyncio
from ..common.identity import PublicKey
#from ..common.tcp_packet import has_full_tcp_packet, decode_tcp_packet, encode_tcp_packet
from ..common.transport_packet import tTransportPacket, encode_transport_packet, decode_transport_packet
#from .remoting import Remoting
from .transport_session import TransportSessionList

log = logging.getLogger(__name__)


class TcpProtocol(asyncio.Protocol):

    _connections = {}  # (server public key, host, port) -> TcpProtocol

    @classmethod
    async def produce(cls, remoting, server_public_key, host, port):
        assert isinstance(remoting, Remoting), repr(remoting)
        key = (server_public_key.get_id(), host, port)
        protocol = cls._connections.get(key)
        if not protocol:
            loop = asyncio.get_event_loop()
            constructor = lambda: cls(remoting, server_public_key, host, port)
            transport, protocol = await loop.create_connection(constructor, host, port)
            cls._connections[key] = protocol
        return protocol

    @staticmethod
    def _make_key(server_public_key, host, port):
        return (server_public_key.get_id(), host, port)

    def __init__(self, remoting, server_public_key, host, port):
        assert isinstance(server_public_key, PublicKey), repr(server_public_key)
        self._remoting = remoting
        self._server_public_key = server_public_key
        self._host = host
        self._port = port
        self.session_list = TransportSessionList()
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

    def _log(self, msg):
        log.info('tcp to %s at %s:%d: %s', self._server_public_key.get_short_id_hex(), self._host, self._port, msg)
        
