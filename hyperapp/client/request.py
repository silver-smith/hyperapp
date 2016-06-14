from ..common.htypes import (
    tClientNotification,
    tRequest,
    tServerPacket,
    tServerNotification,
    tResponse,
    Interface,
    IfaceRegistry,
    )
from ..common.identity import PublicKey


class RequestBase(object):

    def __init__( self, iface, path, command_id, params ):
        assert isinstance(iface, Interface), repr(iface)
        assert isinstance(command_id, str), repr(command_id)
        params_type = iface.get_request_params_type(command_id)
        if params is None:
            params = params_type()
        assert isinstance(params, params_type), repr(params)
        self.iface = iface
        self.path = path
        self.command_id = command_id
        self.params = params


class ClientNotification(RequestBase):

    def to_data( self ):
        return tClientNotification(self.iface.iface_id, self.path, self.command_id, self.params)


class Request(RequestBase):

    def __init__( self, iface, path, command_id, request_id, params=None ):
        assert isinstance(request_id, str), repr(request_id)
        RequestBase.__init__(self, iface, path, command_id, params)
        self.request_id = request_id

    def to_data( self ):
        return tRequest(self.iface.iface_id, self.path, self.command_id, self.params, self.request_id)

    def process_response( self, server, response ):
        raise NotImplementedError(self.__class__)


class ResponseBase(object):

    @classmethod
    def from_data( cls, server_public_key, iface_registry, rec ):
        assert isinstance(iface_registry, IfaceRegistry), repr(iface_registry)
        assert isinstance(rec, tServerPacket), repr(rec)
        
        if isinstance(rec, tResponse):
            iface = iface_registry.resolve(rec.iface)
            return Response(server_public_key, rec.updates, iface, rec.command_id, rec.request_id, rec.result)
        else:
            assert isinstance(rec, tServerNotification), repr(rec)
            return ServerNotification(server_public_key, rec.updates)

    def __init__( self, server_public_key, updates ):
        assert isinstance(server_public_key, PublicKey), repr(server_public_key)
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
