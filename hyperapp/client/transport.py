

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

    def send_packet( self, server, endpoint, packet ):
        for route in endpoint.routes:
            transport_id = route[0]
            transport = self._id2transport.get(transport_id)
            if transport and transport.send_packet(server, route[1:], packet):
                break


transports = TransportRegistry()
