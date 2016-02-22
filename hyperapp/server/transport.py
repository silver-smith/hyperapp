from ..common.transport_packet import tTransportPacket


class Transport(object):

    def process_packet( self, server, peer, transport_packet_data ):
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

    def process_packet( self, server, peer, packet ):
        tTransportPacket.validate('<TransportPacket>', packet)
        transport = self.resolve(packet.transport_id)
        return transport.process_packet(server, peer, packet.data)


transport_registry = TransportRegistry()
