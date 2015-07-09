from . util import is_list_inst
from . interface import TPrimitive, tString, Field, TRecord, TIface, TPath, tUpdateList, Interface
from . interface.dynamic_record import TDynamicRec


class ServerNotification(object):

    packet_type = 'notification'

    def __init__( self, peer, updates=None ):
        self.peer = peer
        self.updates = updates or []  # Update list

    def add_update( self, update ):
        self.updates.append(update)


class Response(ServerNotification):

    packet_type = 'response'

    def __init__( self, peer, iface, command_id, request_id, result=None, updates=None, packet_type=None ):
        ServerNotification.__init__(self, peer, updates)
        self.packet_type = 'response'
        self.iface = iface
        self.command_id = command_id
        self.request_id = request_id
        self.result = result


class ClientNotification(object):

    def __init__( self, peer, iface, path, command_id, params=None ):
        self.peer = peer
        self.iface = iface
        self.path = path
        self.command_id = command_id
        self.params = params
        

class Request(ClientNotification):

    def __init__( self, peer, iface, path, command_id, request_id, params=None ):
        ClientNotification.__init__(self, peer, iface, path, command_id, params)
        self.request_id = request_id

    def make_response( self, result=None ):
        result_type = self.iface.get_command_result_type(self.command_id)
        result_type.validate(self.iface.iface_id +  '.Request.result', result)
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


class TServerPacket(TDynamicRec):

    def __init__( self ):
        fields = [
            Field('updates', tUpdateList),
            Field('packet_type', tString),
            ]
        TDynamicRec.__init__(self, fields)

    def resolve_dynamic( self, rec ):
        if rec.packet_type == Response.packet_type:
            return TResponse(self)
        if rec.packet_type == ServerNotification.packet_type:
            return TRecord(base=self, cls=ServerNotification)
        assert False, repr(rec.packet_type)  # unknown packet type


class TResponse(TDynamicRec):

    def __init__( self, base ):
        fields = [
            Field('iface', TIface()),
            Field('command_id', tString),
            Field('request_id', tString),
            ]
        TDynamicRec.__init__(self, fields, base=base)

    def resolve_dynamic( self, rec ):
        fields = [Field('result', rec.iface.get_command_result_type(rec.command_id))]
        return TRecord(fields, cls=Response, base=self, want_peer_arg=True)


class TClientPacket(TDynamicRec):

    def __init__( self ):
        fields = [
            Field('iface', TIface()),
            Field('path', TPath()),
            Field('command_id', tString),
            ]
        TDynamicRec.__init__(self, fields)

    def resolve_dynamic( self, rec ):
        request_type = rec.iface.get_request_type(rec.command_id)
        params_type = rec.iface.get_request_params_type(rec.command_id)
        params_field = Field('params', params_type)
        if request_type == Interface.rt_request:
            return TRecord(base=self, cls=Request, want_peer_arg=True, fields=[
                params_field,
                Field('request_id', tString),
                ])
        if request_type == Interface.rt_notification:
            return TRecord(fields=[params_field], base=self, cls=ClientNotification, want_peer_arg=True)
        assert False, repr(request_type)  # Unexpected request type


tServerPacket = TServerPacket()
tClientPacket = TClientPacket()
