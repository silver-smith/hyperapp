from ..common.htypes import (
    Interface,
    IfaceRegistry,
    )
from ..common.identity import PublicKey


class RequestBase(object):

    def __init__(self, request_types, iface, path, command_id, params):
        assert isinstance(iface, Interface), repr(iface)
        assert isinstance(command_id, str), repr(command_id)
        params_type = iface.get_request_params_type(command_id)
        if params is None:
            params = params_type()
        assert isinstance(params, params_type), repr(params)
        self._request_types = request_types
        self.iface = iface
        self.path = path
        self.command_id = command_id
        self.params = params


class ClientNotification(RequestBase):

    def to_data(self):
        return self._request_types.client_notification(self.iface.iface_id, self.path, self.command_id, self.params)


class Request(RequestBase):

    def __init__(self, request_types, iface, path, command_id, request_id, params=None):
        assert isinstance(request_id, str), repr(request_id)
        RequestBase.__init__(self, request_types, iface, path, command_id, params)
        self.request_id = request_id

    def to_data(self):
        return self._request_types.request(self.iface.iface_id, self.path, self.command_id, self.params, self.request_id)


class ResponseBase(object):

    @classmethod
    def from_data(cls, request_types, iface_registry, server_public_key, rec):
        assert isinstance(iface_registry, IfaceRegistry), repr(iface_registry)
        assert isinstance(rec, request_types.server_packet), repr(rec)
        
        if isinstance(rec, request_types.response):
            iface = iface_registry.resolve(rec.iface)
            result = error = None
            if isinstance(rec, request_types.result_response):
                result = rec.result
            if isinstance(rec, request_types.error_response):
                error = rec.error
            return Response(request_types, server_public_key, rec.updates, iface, rec.command_id, rec.request_id, result, error)
        else:
            assert isinstance(rec, request_types.server_notification), repr(rec)
            return ServerNotification(request_types, server_public_key, rec.updates)

    def __init__(self, request_types, server_public_key, updates):
        assert isinstance(server_public_key, PublicKey), repr(server_public_key)
        self._request_types = request_types
        self.server_public_key = server_public_key
        self.updates = updates


class ServerNotification(ResponseBase):
    pass


class Response(ResponseBase):

    def __init__(self, request_types, server_public_key, updates, iface, command_id, request_id, result=None, error=None):
        ResponseBase.__init__(self, request_types, server_public_key, updates)
        self.iface = iface
        self.command_id = command_id
        self.request_id = request_id
        self.result = result
        self.error = error  # exception
