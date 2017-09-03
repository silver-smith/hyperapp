from ..common.util import is_list_inst
from ..common.htypes import (
    EncodableEmbedded,
    tEmbedded,
    Interface,
    IfaceRegistry,
    )
from ..common.request import Update
from ..common.identity import PublicKey


class RequestBase(object):

    def __init__(self, packet_types, iface, path, command_id, params):
        assert isinstance(iface, Interface), repr(iface)
        assert isinstance(command_id, str), repr(command_id)
        params_type = iface.get_command(command_id).params_type
        if params is None:
            params = params_type()
        assert isinstance(params, params_type), repr((params, params_type))
        self._packet_types = packet_types
        self.iface = iface
        self.path = path
        self.command_id = command_id
        self.params = params

    def __eq__(self, other):
        return (isinstance(other, RequestBase) and
                self.iface is other.iface and
                self.path == other.path and
                self.command_id == other.command_id and
                self.params == other.params)

    @property
    def _command(self):
        return self.iface.get_command(self.command_id)

    @property
    def _params_t(self):
        return self._command.params_type

    @property
    def _embedded_params(self):
        return EncodableEmbedded(self._params_t, self.params)


class ClientNotification(RequestBase):

    def to_data(self):
        return self._packet_types.client_notification(self._command.iface.iface_id, self.path, self.command_id, self._embedded_params)


    def __eq__(self, other):
        return (isinstance(other, ClientNotification) and
                RequestBase.__eq__(self, other))


class Request(RequestBase):

    def __init__(self, packet_types, iface, path, command_id, request_id, params=None):
        assert isinstance(request_id, str), repr(request_id)
        RequestBase.__init__(self, packet_types, iface, path, command_id, params)
        self.request_id = request_id

    def to_data(self):
        return self._packet_types.client_request(self._command.iface.iface_id, self.path, self.command_id, self._embedded_params, self.request_id)

    def __repr__(self):
        return '<Request iface=%s path=%s command_id=%s params=%s request_id=%s>' % (
            self.iface.iface_id, self.path, self.command_id, self.params, self.request_id)


    def __eq__(self, other):
        return (isinstance(other, Request) and
                RequestBase.__eq__(self, other) and
                self.request_id == other.request_id)


class ResponseBase(object):

    @classmethod
    def from_data(cls, packet_types, iface_registry, server_public_key, rec):
        assert isinstance(iface_registry, IfaceRegistry), repr(iface_registry)
        assert isinstance(rec, packet_types.server_packet), repr(rec)

        updates = [Update.from_data(iface_registry, update) for update in rec.update_list]

        if isinstance(rec, packet_types.server_response):
            iface = iface_registry.resolve(rec.iface)
            result = error = None
            if isinstance(rec, packet_types.server_result_response):
                result = rec.result.decode(iface.get_command(rec.command_id).result_type)
            if isinstance(rec, packet_types.server_error_response):
                error = rec.error.decode(packet_types.error)
            return Response(packet_types, server_public_key, updates, iface, rec.command_id, rec.request_id, result, error)
        if isinstance(rec, packet_types.server_notification):
            return ServerNotification(packet_types, server_public_key, updates)
        assert False, 'Unsupported packet type: %s' % rec

    def __init__(self, packet_types, server_public_key, updates):
        assert isinstance(server_public_key, PublicKey), repr(server_public_key)
        assert is_list_inst(updates, Update), repr(updates)
        self._packet_types = packet_types
        self.server_public_key = server_public_key
        self.updates = updates


class ServerNotification(ResponseBase):
    pass


class Response(ResponseBase):

    def __init__(self, packet_types, server_public_key, updates, iface, command_id, request_id, result=None, error=None):
        ResponseBase.__init__(self, packet_types, server_public_key, updates)
        self.iface = iface
        self.command_id = command_id
        self.request_id = request_id
        self.result = result
        self.error = error  # exception
