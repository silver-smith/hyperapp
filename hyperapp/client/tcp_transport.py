from ..common.packet import Packet
from ..common.transport_packet import encode_transport_packet
from ..common.packet_coders import packet_coders
from ..common.packet import tAuxInfo, AuxInfo, tPacket, Packet
from .transport import Transport, transports
from .tcp_connection import TcpConnection


CDR_TRANSPORT_ID = 'tcp.cdr'
JSON_TRANSPORT_ID = 'tcp.json'


class DataConsumer(object):

    def __init__( self, server ):
        self.server = server

    def __call__( self, data ):
        if not Packet.has_full_packet(data):
            return None
        packet, packet_size = Packet.decode(data)
        print 'received %s packet' % packet.encoding
        self.server.process_packet(packet)
        return packet_size


class TcpTransport(Transport):

    connections = {}  # (server public key, host, port) -> Connection

    def __init__( self, transport_id, encoding ):
        self.transport_id = transport_id
        self.encoding = encoding

    def register( self ):
        transports.register(self.transport_id, self)

    def send_packet( self, server, route, payload, payload_type, aux_info ):
        assert len(route) >= 2, repr(route)  # host and port are expected
        host, port_str = route[:2]
        port = int(port_str)
        connection = self._produce_connection(server, host, port)
        packet = self._make_packet(payload, payload_type, aux_info)
        connection.send_data(packet)
        return True

    def _make_packet( self, payload, payload_type, aux_info ):
        if aux_info is None:
            aux_info = AuxInfo(requirements=[], modules=[])
        packet_data = packet_coders.encode(self.encoding, payload, payload_type)
        packet = Packet(aux_info, packet_data)
        encoded_packet = packet_coders.encode(self.encoding, packet, tPacket)
        return encode_transport_packet(self.transport_id, encoded_packet)

    def _produce_connection( self, server, host, port ):
        key = (server.endpoint.public_key, host, port)
        connection = self.connections.get(key)
        if not connection:
            connection = TcpConnection(host, port, DataConsumer(server))
            self.connections[key] = connection
        return connection


TcpTransport(CDR_TRANSPORT_ID, 'cdr').register()
TcpTransport(JSON_TRANSPORT_ID, 'json').register()
