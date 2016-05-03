from ..common.transport_packet import tTransportPacket
from .transport_session import TransportSessionList



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

    def process_packet( self, iface_registry, server, session_list, request_packet ):
        assert isinstance(session_list, TransportSessionList), repr(session_list)
        tTransportPacket.validate('<TransportPacket>', request_packet)
        transport = self.resolve(request_packet.transport_id)
        responses = transport.process_packet(iface_registry, server, session_list, request_packet.data)
        return [tTransportPacket(request_packet.transport_id, response_data)
                for response_data in responses]
        


transport_registry = TransportRegistry()
