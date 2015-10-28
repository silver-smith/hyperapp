from ..common.interface import tClientPacket, tClientNotification, tRequest, tResponse


class RequestBase(object):

    @classmethod
    def from_request_rec( cls, me, peer, iface_registry, rec ):
        tClientPacket.validate('<ClientNotification>', rec)
        iface = iface_registry.resolve(rec.iface)
        if tClientPacket.isinstance(rec, tRequest):
            return Request(me, peer, iface, rec.path, rec.command_id, rec.request_id, rec.params)
        else:
            assert tClientPacket.isinstance(rec, tClientNotification), repr(rec)
            return ClientNotification(me, peer, iface, rec.path, rec.command_id, rec.params)

    def __init__( self, me, peer, iface, path, command_id, params ):
        self.me = me
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
        result_type.validate('%s.Request.%s.result' % (self.iface.iface_id, self.command_id), result)
        return Response(self.peer, self.iface, self.command_id, self.request_id, result)

    def make_response_object( self, obj ):
        return self.make_response(obj)

    def make_response_handle( self, obj ):
        return self.make_response(obj.get_handle())

    def make_response_result( self, **kw ):
        return self.make_response(self.iface.make_result(self.command_id, **kw))

    def make_response_update( self, iface, path, diff ):
        response = self.make_response()
        response.add_update(iface.Update(path, diff))
        return response


class Response(object):

    def __init__( self, peer, iface, command_id, request_id, result ):
        self.peer = peer
        self.iface = iface
        self.command_id = command_id
        self.request_id = request_id
        self.result = result

    def encode( self ):
        return tResponse.instantiate(self.iface.iface_id, self.command_id, self.request_id, self.result)
