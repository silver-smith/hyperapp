from ..common.interface import tClientNotification, tRequest, Interface


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
