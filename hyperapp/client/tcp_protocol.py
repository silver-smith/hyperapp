import logging
import asyncio
from ..common.identity import PublicKey
from ..common.tcp_packet import has_full_tcp_packet, decode_tcp_packet, encode_tcp_packet

log = logging.getLogger(__name__)


class TcpProtocol(asyncio.Protocol):

    _connections = {}  # (server public key, host, port) -> TcpProtocol

    @classmethod
    @asyncio.coroutine
    def produce( cls, server_public_key, host, port ):
        key = (server_public_key.get_id(), host, port)
        protocol = cls._connections.get(key)
        if not protocol:
            loop = asyncio.get_event_loop()
            constructor = lambda: cls(server_public_key, host, port)
            transport, protocol = yield from loop.create_connection(constructor, host, port)
            cls._connections[key] = protocol
        return protocol

    @staticmethod
    def _make_key( server_public_key, host, port ):
        return (server_public_key.get_id(), host, port)

    def __init__( self, server_public_key, host, port ):
        assert isinstance(server_public_key, PublicKey), repr(server_public_key)
        self.server_public_key = server_public_key
        self.host = host
        self.port = port

    def connection_made( self, transport ):
        log.info('tcp connection made')
        self.transport = transport

    def send_data( self, contents ):
        assert isinstance(contents, bytes), repr(contents)
        data = encode_tcp_packet(contents)
        self._log('sending data, size=%d' % len(data))
        self.transport.write(data)

    def _log( self, msg ):
        log.info('tcp to %s at %s:%d: %s', self.server_public_key.get_short_id_hex(), self.host, self.port, msg)
        
