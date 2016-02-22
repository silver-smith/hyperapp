from ..common.transport_packet import tTransportPacket


class Transport(object):

    def send_packet( self, server, route, packet ):
        raise NotImplementedError(self.__class__)


class TransportRegistry(object):

    def __init__( self ):
        self._id2transport = {}

    def register( self, id, transport ):
        assert isinstance(id, str), repr(id)
        assert isinstance(transport, Transport), repr(transport)
        self._id2transport[id] = transport

    def resolve( self, id ):
        return self._id2transport[id]

    def send_packet( self, server, payload, payload_type, aux_info=None ):
        for route in server.get_endpoint().routes:
            transport_id = route[0]
            transport = self._id2transport.get(transport_id)
            if not transport:
                print 'Warning: unknown transport: %r' % transport_id
                continue
            if transport.send_packet(server, route[1:], payload, payload_type, aux_info):
                return
        raise RuntimeError('Unable to send packet to %s - no reachable transports'
                           % server.get_endpoint().public_key.get_short_id_hex())

    def process_packet( self, packet ):
        tTransportPacket.validate('<TransportPacket>', packet)
        transport = self.resolve(packet.transport_id)
        transport.process_packet(packet.data)
        

transport_registry = TransportRegistry()
