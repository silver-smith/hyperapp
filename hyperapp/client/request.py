from ..common.interface import (
    tClientNotification,
    tRequest,
    tServerPacket,
    tServerNotification,
    tResponse,
    Interface,
    )


class RequestBase(object):

    def __init__( self, server, iface, path, command_id, params ):
        assert isinstance(iface, Interface), repr(iface)
        iface.validate_request(command_id, params)
        self.server = server
        self.iface = iface
        self.path = path
        self.command_id = command_id
        self.params = params


class ClientNotification(RequestBase):

    def encode( self ):
        return tClientNotification.instantiate(self.iface.iface_id, self.path, self.command_id, self.params)


class Request(RequestBase):

    def __init__( self, server, iface, path, command_id, request_id, params=None ):
        RequestBase.__init__(self, server, iface, path, command_id, params)
        self.request_id = request_id

    def encode( self ):
        return tRequest.instantiate(self.iface.iface_id, self.path, self.command_id, self.params, self.request_id)


class ResponseBase(object):

    @classmethod
    def from_response_rec( cls, server, iface_registry, rec ):
        tServerPacket.validate('<ServerPacket>', rec)
        iface = iface_registry.resolve(rec.iface)
        if tServerPacket.isinstance(rec, tResponse):
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
