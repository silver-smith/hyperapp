from ..common.packet import Packet
from .transport import Transport, transports
from .tcp_connection import TcpConnection


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

    def send_packet( self, server, route, packet ):
        assert len(route) >= 2, repr(route)  # host and port are expected
        host, port_str = route[:2]
        port = int(port_str)
        connection = self._produce_connection(server, host, port)
        connection.send_data(packet.encode())

    def _produce_connection( self, server, host, port ):
        key = (server.endpoint.public_key, host, port)
        connection = self.connections.get(key)
        if not connection:
            connection = TcpConnection(host, port, DataConsumer(server))
            self.connections[key] = connection
        return connection


transports.register('tcp', TcpTransport())
