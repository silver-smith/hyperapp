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

    def process_packet( self, iface_registry, server, peer, request_packet ):
        tTransportPacket.validate('<TransportPacket>', request_packet)
        transport = self.resolve(request_packet.transport_id)
        response_data = transport.process_packet(iface_registry, server, peer, request_packet.data)
        if response_data is None:
            return None
        return tTransportPacket.instantiate(request_packet.transport_id, response_data)
        


transport_registry = TransportRegistry()
