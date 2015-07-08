from . util import is_list_inst
from . interface import TPrimitive, TString, Field, TRecord, TIface, TPath, tUpdateList
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


class TServerPacket(TDynamicRec):

    def __init__( self ):
        fields = [
            Field('updates', tUpdateList),
            Field('packet_type', TString()),
            ]
        TDynamicRec.__init__(self, fields)

    def resolve_dynamic( self, rec ):
        if rec.packet_type == Response.packet_type:
            return tResponse
        if rec.packet_type == ServerNotification.packet_type:
            return tServerNotification
        assert False, repr(rec.packet_type)  # unknown packet type


class TResponse(TDynamicRec):

    def __init__( self ):
        fields = [
            Field('iface', TIface()),
            Field('command_id', TString()),
            Field('request_id', TString()),
            ]
        TDynamicRec.__init__(self, fields, base=tServerPacket)

    def resolve_dynamic( self, rec ):
        fields = [Field('result', rec.iface.get_command_result_type(rec.command_id))]
        return TRecord(fields, cls=Response, base=self)


tServerPacket = TServerPacket()
tResponse = TResponse()
tServerNotification = TRecord(base=tServerPacket, cls=ServerNotification)


class ClientNotification(object):

    def __init__( self, peer, iface, path, command_id, params=None ):
        self.peer = peer
        self.iface = iface
        self.path = path
        self.command_id = command_id
        self.params = params or {}

    def encode( self, encoder ):
        return encoder.encode(self.get_packet_type(), self)

    def get_packet_type( self ):
        return self.iface.get_client_notification_type(self.command_id)
        

class Request(ClientNotification):

    def __init__( self, peer, iface, path, command_id, request_id, params=None ):
        ClientNotification.__init__(self, peer, iface, path, command_id, params)
        self.request_id = request_id

    def get_packet_type( self ):
        return self.iface.get_request_type(self.command_id)

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


class TClientNotification(TPrimitive):
    type_name = 'client_notification'
    type = ClientNotification

class TRequest(TPrimitive):
    type_name = 'request'
    type = Request
