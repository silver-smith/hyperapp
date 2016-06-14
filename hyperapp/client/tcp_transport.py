import asyncio
from ..common.htypes import tClientPacket, tServerPacket
from ..common.packet import tAuxInfo, tPacket
from ..common.transport_packet import tTransportPacket
from ..common.packet_coders import packet_coders
from .transport import Transport, transport_registry
from .tcp_protocol import TcpProtocol


CDR_TRANSPORT_ID = 'tcp.cdr'
JSON_TRANSPORT_ID = 'tcp.json'


class TcpTransport(Transport):

    def __init__( self, transport_id, encoding ):
        self.transport_id = transport_id
        self.encoding = encoding

    def register( self ):
        transport_registry.register(self.transport_id, self)

    @asyncio.coroutine
    def send_request_rec( self, endpoint, route, request_or_notification ):
        assert len(route) >= 2, repr(route)  # host and port are expected
        host, port_str = route[:2]
        port = int(port_str)
        transport_packet = self._make_transport_packet(request_or_notification)
        protocol = yield from TcpProtocol.produce(endpoint.public_key, host, port)
        protocol.send_packet(transport_packet)
        return True

    def process_packet( self, connection, session_list, server_public_key, data ):
        packet = packet_coders.decode(self.encoding, data, tPacket)
        app = QtCore.QCoreApplication.instance()
        app.response_mgr.process_packet(server_public_key, packet, self._decode_payload)

    def _decode_payload( self, data ):
        return packet_coders.decode(self.encoding, data, tServerPacket)

    def _make_transport_packet( self, request_or_notification ):
        aux_info = tAuxInfo(requirements=[], modules=[])  # not used in packets from client
        packet_data = packet_coders.encode(self.encoding, request_or_notification.to_data(), tClientPacket)
        packet = tPacket(aux_info, packet_data)
        encoded_packet = packet_coders.encode(self.encoding, packet, tPacket)
        return tTransportPacket(self.transport_id, encoded_packet)


TcpTransport(CDR_TRANSPORT_ID, 'cdr').register()
TcpTransport(JSON_TRANSPORT_ID, 'json').register()
