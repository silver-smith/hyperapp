from ..common.interface import (
    tClientNotification,
    tRequest,
    tServerPacket,
    tServerNotification,
    tResponse,
    Interface,
    )


class RequestBase(object):

    def __init__( self, iface, path, command_id, params ):
        assert isinstance(iface, Interface), repr(iface)
        assert isinstance(command_id, basestring), repr(command_id)
        iface.validate_request(command_id, params)
        self.iface = iface
        self.path = path
        self.command_id = command_id
        self.params = params


class ClientNotification(RequestBase):

    def encode( self ):
        return tClientNotification.instantiate(self.iface.iface_id, self.path, self.command_id, self.params)


class Request(RequestBase):

    def __init__( self, iface, path, command_id, params=None ):
        RequestBase.__init__(self, iface, path, command_id, params)

    def encode( self, request_id ):
        assert isinstance(request_id, str), repr(request_id)
        return tRequest.instantiate(self.iface.iface_id, self.path, self.command_id, self.params, request_id)

    def process_response( self, server, response ):
        raise NotImplementedError(self.__class__)


class ResponseBase(object):

    @classmethod
    def from_response_rec( cls, server, iface_registry, rec ):
        tServerPacket.validate('<ServerPacket>', rec)
        if tServerPacket.isinstance(rec, tResponse):
            iface = iface_registry.resolve(rec.iface)
            return Response(server, rec.updates, iface, rec.command_id, rec.request_id, rec.result)
        else:
            assert tServerPacket.isinstance(rec, tServerNotification), repr(rec)
            return ServerNotification(server, rec.updates)

    def __init__( self, server, updates ):
        self.server = server
        self.updates = updates


class ServerNotification(ResponseBase):
    pass


class Response(ResponseBase):

    def __init__( self, server, updates, iface, command_id, request_id, result ):
        ResponseBase.__init__(self, server, updates)
        self.iface = iface
        self.command_id = command_id
        self.request_id = request_id
        self.result = result
