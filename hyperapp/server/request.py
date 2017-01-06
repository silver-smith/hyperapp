from ..common.util import is_list_inst
from ..common.identity import PublicKey
from ..common.url import Url


class NotAuthorizedError(Exception):

    def __init__( self, public_key ):
        Exception.__init__(self, 'Authorization required for %s' % public_key.get_short_id_hex())
        self.public_key = public_key


class PeerChannel(object):

    def get_id( self ):
        return hex(id(self))[-6:]

    def send_update( self, update ):
        raise NotImplementedError(self.__class__)

    def pop_updates( self ):
        raise NotImplementedError(self.__class__)


class Peer(object):

    def __init__( self, channel, public_keys=None ):
        assert isinstance(channel, PeerChannel), repr(channel)
        assert public_keys is None or is_list_inst(public_keys, PublicKey), repr(public_keys)
        self.channel = channel
        self.public_keys = public_keys or []


class RequestBase(object):

    @classmethod
    def from_data( cls, me, peer, request_types, core_types, iface_registry, rec ):
        assert isinstance(peer, Peer), repr(peer)
        assert isinstance(rec, request_types.tClientPacket), repr(rec)
        iface = iface_registry.resolve(rec.iface)
        if isinstance(rec, request_types.tRequest):
            return Request(request_types, core_types, me, peer, iface, rec.path, rec.command_id, rec.request_id, rec.params)
        else:
            assert isinstance(rec, request_types.tClientNotification), repr(rec)
            return ClientNotification(request_types, core_types, me, peer, iface, rec.path, rec.command_id, rec.params)

    def __init__( self, request_types, core_types, me, peer, iface, path, command_id, params ):
        self._request_types = request_types
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

    def __init__( self, request_types, core_types, me, peer, iface, path, command_id, request_id, params ):
        RequestBase.__init__(self, request_types, core_types, me, peer, iface, path, command_id, params)
        self.request_id = request_id

    def make_response( self, result=None ):
        result_type = self.iface.get_command_result_type(self.command_id)
        if result is None:
            result = result_type()
        assert isinstance(result, result_type), \
          '%s.Request.%s.result is expected to be %r, but is %r' % (self.iface.iface_id, self.command_id, result_type, result)
        return Response(self._request_types, self.peer, self.iface, self.command_id, self.request_id, result)

    def make_response_object( self, obj ):
        return self.make_response_handle(obj.get_handle(self))

    def make_response_handle( self, handle ):
        return self.make_response_result(handle=handle)
    
    def make_response_result( self, **kw ):
        return self.make_response(self.iface.make_result(self.command_id, **kw))

    def make_response_update( self, iface, path, diff ):
        response = self.make_response()
        response.add_update(iface.Update(path, diff))
        return response

    def make_response_redirect( self, url ):
        assert isinstance(url, Url), repr(url)
        return self.make_response_handle(self._core_types.redirect_handle(
            view_id='redirect', redirect_to=url.to_data()))


class ResponseBase(object):

    def __init__( self, request_types ):
        self._request_types = request_types
        self.updates = []

    def add_update( self, update ):
        assert isinstance(update, self._request_types.tUpdate), repr(update)
        self.updates.append(update)


class ServerNotification(ResponseBase):

    def to_data( self ):
        return self._request_types.tServerNotification(self.updates)


class Response(ResponseBase):

    def __init__( self, request_types, peer, iface, command_id, request_id, result ):
        assert isinstance(peer, Peer), repr(peer)
        ResponseBase.__init__(self, request_types)
        self.peer = peer
        self.iface = iface
        self.command_id = command_id
        self.request_id = request_id
        self.result = result

    def to_data( self ):
        return self._request_types.tResponse(self.updates, self.iface.iface_id, self.command_id, self.request_id, self.result)
