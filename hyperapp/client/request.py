from ..common.htypes import (
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

    def to_data( self ):
        return tClientNotification.instantiate(self.iface.iface_id, self.path, self.command_id, self.params)


class Request(RequestBase):

    def __init__( self, iface, path, command_id, params=None ):
        RequestBase.__init__(self, iface, path, command_id, params)

    def to_data( self, request_id ):
        assert isinstance(request_id, str), repr(request_id)
        return tRequest.instantiate(self.iface.iface_id, self.path, self.command_id, self.params, request_id)

    def process_response( self, server, response ):
        raise NotImplementedError(self.__class__)


class ResponseBase(object):

    @classmethod
    def from_data( cls, server_public_key, iface_registry, rec ):
        tServerPacket.validate('<ServerPacket>', rec)
        if tServerPacket.isinstance(rec, tResponse):
            iface = iface_registry.resolve(rec.iface)
            return Response(server_public_key, rec.updates, iface, rec.command_id, rec.request_id, rec.result)
        else:
            assert tServerPacket.isinstance(rec, tServerNotification), repr(rec)
            return ServerNotification(server, rec.updates)

    def __init__( self, server_public_key, updates ):
        self.server_public_key = server_public_key
        self.updates = updates


class ServerNotification(ResponseBase):
    pass


class Response(ResponseBase):

    def __init__( self, server_public_key, updates, iface, command_id, request_id, result ):
        ResponseBase.__init__(self, server_public_key, updates)
        self.iface = iface
        self.command_id = command_id
        self.request_id = request_id
        self.result = result
