from ..common.util import is_list_inst
from ..common.htypes import EncodableEmbedded
from ..common.request import Update
from ..common.identity import PublicKey
from ..common.url import Url


class NotAuthorizedError(Exception):

    def __init__(self, public_key):
        Exception.__init__(self, 'Authorization required for %s' % public_key.get_short_id_hex())
        self.public_key = public_key


class PeerChannel(object):

    def get_id(self):
        return hex(id(self))[-6:]

    def send_update(self, update):
        raise NotImplementedError(self.__class__)

    def pop_updates(self):
        raise NotImplementedError(self.__class__)


class Peer(object):

    def __init__(self, channel, public_keys=None):
        assert isinstance(channel, PeerChannel), repr(channel)
        assert public_keys is None or is_list_inst(public_keys, PublicKey), repr(public_keys)
        self.channel = channel
        self.public_keys = public_keys or []


class RequestBase(object):

    @classmethod
    def from_data(cls, me, peer, packet_types, core_types, iface_registry, rec):
        assert isinstance(peer, Peer), repr(peer)
        assert isinstance(rec, packet_types.client_packet), repr(rec)
        iface = iface_registry.resolve(rec.iface)
        params = rec.params.decode(iface.get_command(rec.command_id).params_type)
        if isinstance(rec, packet_types.client_request):
            return Request(packet_types, core_types, me, peer, iface, rec.path, rec.command_id, params, rec.request_id)
        if isinstance(rec, packet_types.client_notification):
            return ClientNotification(packet_types, core_types, me, peer, iface, rec.path, rec.command_id, params)
        assert False, 'Unsupported packet type: %s' % rec

    def __init__(self, packet_types, core_types, me, peer, iface, path, command_id, params):
        self._packet_types = packet_types
        self._core_types = core_types
        self.me = me      # Server instance
        self.peer = peer
        self.iface = iface
        self.path = path
        self.command_id = command_id
        self.params = params


class ClientNotification(RequestBase):
    pass


class Request(RequestBase):

    def __init__(self, packet_types, core_types, me, peer, iface, path, command_id, params, request_id):
        RequestBase.__init__(self, packet_types, core_types, me, peer, iface, path, command_id, params)
        self.request_id = request_id

    def make_response(self, result=None, error=None):
        result_type = self.iface.get_command(self.command_id).result_type
        if result is None and error is None:
            result = result_type()
        assert result is None or isinstance(result, result_type), \
          '%s.Request.%s.result is expected to be %r, but is %r' % (self.iface.iface_id, self.command_id, result_type, result)
        return Response(self._packet_types, self.peer, self.iface, self.command_id, self.request_id, result, error)

    def make_response_object(self, obj):
        return self.make_response_handle(obj.get_handle(self))

    def make_response_handle(self, handle):
        return self.make_response_result(handle=handle)
    
    def make_response_result(self, **kw):
        return self.make_response(self.iface.make_result(self.command_id, **kw))

    def make_response_update(self, iface, path, diff):
        response = self.make_response()
        response.add_update(iface.Update(path, diff))
        return response

    def make_response_redirect(self, url):
        assert isinstance(url, Url), repr(url)
        return self.make_response_handle(self._core_types.redirect_handle(
            view_id='redirect', redirect_to=url.to_data()))


class ResponseBase(object):

    def __init__(self, packet_types):
        self._packet_types = packet_types
        self.updates = []

    def add_update(self, update):
        assert isinstance(update, Update), repr(update)
        self.updates.append(update)

    @property
    def _encoded_updates(self):
        return list(map(self._encode_update, self.updates))

    def _encode_update(self, update):
        return self._packet_types.update(
            update.iface.iface_id,
            update.path,
            EncodableEmbedded(update.iface.diff_type, update.diff),
            )


class ServerNotification(ResponseBase):

    def to_data(self):
        return self._packet_types.server_notification(self._encoded_updates)


class Response(ResponseBase):

    def __init__(self, packet_types, peer, iface, command_id, request_id, result=None, error=None):
        assert isinstance(peer, Peer), repr(peer)
        ResponseBase.__init__(self, packet_types)
        self.peer = peer
        self.iface = iface
        self.command_id = command_id
        self.request_id = request_id
        self.result = result
        self.error = error

    def to_data(self):
        if self.error is not None:
            error = EncodableEmbedded(self._packet_types.error, self.error)
            return self._packet_types.server_error_response(self._encoded_updates, self.iface.iface_id, self.command_id, self.request_id, error)
        else:
            result = EncodableEmbedded(self.iface.get_command(self.command_id).result_type, self.result)
            return self._packet_types.server_result_response(self._encoded_updates, self.iface.iface_id, self.command_id, self.request_id, result)
