from ..common.util import is_list_inst
from ..common.htypes import tUpdate, tClientPacket, tClientNotification, tRequest, tServerNotification, tResponse
from ..common.identity import PublicKey


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
    def from_data( cls, me, peer, iface_registry, rec ):
        assert isinstance(peer, Peer), repr(peer)
        assert isinstance(rec, tClientPacket), repr(rec)
        iface = iface_registry.resolve(rec.iface)
        if isinstance(rec, tRequest):
            return Request(me, peer, iface, rec.path, rec.command_id, rec.request_id, rec.params)
        else:
            assert isinstance(rec, tClientNotification), repr(rec)
            return ClientNotification(me, peer, iface, rec.path, rec.command_id, rec.params)

    def __init__( self, me, peer, iface, path, command_id, params ):
        self.me = me      # Server instance
        self.peer = peer
        self.iface = iface
        self.path = path
        self.command_id = command_id
        self.params = params


class ClientNotification(RequestBase):
    pass


class Request(RequestBase):

    def __init__( self, me, peer, iface, path, command_id, request_id, params ):
        RequestBase.__init__(self, me, peer, iface, path, command_id, params)
        self.request_id = request_id

    def make_response( self, result=None ):
        result_type = self.iface.get_command_result_type(self.command_id)
        if result is None:
            result = result_type()
        assert isinstance(result, result_type), \
          '%s.Request.%s.result is expected to be %r, but is %r' % (self.iface.iface_id, self.command_id, result_type, result)
        return Response(self.peer, self.iface, self.command_id, self.request_id, result)

    def make_response_object( self, obj ):
        return self.make_response(obj)

    def make_response_handle( self, obj ):
        return self.make_response(obj.get_handle(self))

    def make_response_result( self, **kw ):
        return self.make_response(self.iface.make_result(self.command_id, **kw))

    def make_response_update( self, iface, path, diff ):
        response = self.make_response()
        response.add_update(iface.Update(path, diff))
        return response



class ResponseBase(object):

    def __init__( self ):
        self.updates = []

    def add_update( self, update ):
        assert isinstance(update, tUpdate), repr(update)
        self.updates.append(update)


class ServerNotification(ResponseBase):

    def to_data( self ):
        return tServerNotification(self.updates)


class Response(ResponseBase):

    def __init__( self, peer, iface, command_id, request_id, result ):
        assert isinstance(peer, Peer), repr(peer)
        ResponseBase.__init__(self)
        self.peer = peer
        self.iface = iface
        self.command_id = command_id
        self.request_id = request_id
        self.result = result

    def to_data( self ):
        return tResponse(self.updates, self.iface.iface_id, self.command_id, self.request_id, self.result)
