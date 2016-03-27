from PySide import QtCore
from ..common.htypes import tServerPacket
from ..common.packet import tAuxInfo, AuxInfo, tPacket, Packet
from ..common.transport_packet import tTransportPacket, encode_transport_packet, decode_transport_packet
from ..common.packet_coders import packet_coders
from .transport import Transport, transport_registry
from .tcp_connection import TcpConnection


CDR_TRANSPORT_ID = 'tcp.cdr'
JSON_TRANSPORT_ID = 'tcp.json'


class TcpTransport(Transport):

    def __init__( self, transport_id, encoding ):
        self.transport_id = transport_id
        self.encoding = encoding

    def register( self ):
        transport_registry.register(self.transport_id, self)

    def send_packet( self, server, route, payload, payload_type, aux_info ):
        assert len(route) >= 2, repr(route)  # host and port are expected
        host, port_str = route[:2]
        port = int(port_str)
        packet = self._make_packet(payload, payload_type, aux_info)
        connection = TcpConnection.produce(server.endpoint.public_key, host, port)
        connection.send_data(packet)
        return True

    def process_packet( self, session_list, server_public_key, data ):
        packet = packet_coders.decode(self.encoding, data, tPacket)
        app = QtCore.QCoreApplication.instance()
        app.response_mgr.process_packet(server_public_key, packet, self._decode_payload)

    def _decode_payload( self, data ):
        return packet_coders.decode(self.encoding, data, tServerPacket)

    def _make_packet( self, payload, payload_type, aux_info ):
        if aux_info is None:
            aux_info = AuxInfo(requirements=[], modules=[])
        packet_data = packet_coders.encode(self.encoding, payload, payload_type)
        packet = Packet(aux_info, packet_data)
        encoded_packet = packet_coders.encode(self.encoding, packet, tPacket)
        transport_packet = tTransportPacket.instantiate(self.transport_id, encoded_packet)
        return encode_transport_packet(transport_packet)


TcpTransport(CDR_TRANSPORT_ID, 'cdr').register()
TcpTransport(JSON_TRANSPORT_ID, 'json').register()
