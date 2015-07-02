import pprint
from . util import is_list_inst, dt2local_str


class ColumnType(object):

    def to_string( self, value ):
        raise NotImplementedError(self.__class__)


class StrColumnType(ColumnType):

    id = 'str'

    def to_string( self, value ):
        return value


class DateTimeColumnType(ColumnType):

    id = 'datetime'

    def to_string( self, value ):
        return dt2local_str(value)


class ServerNotification(object):

    def __init__( self, peer, updates=None ):
        self.peer = peer
        self.updates = updates or []  # Update list

    def add_update( self, update ):
        self.updates.append(update)

    def as_dict( self ):
        return dict(updates=self.updates)


class Response(ServerNotification):

    def __init__( self, peer, iface, command_id, request_id, result=None, updates=None ):
        ServerNotification.__init__(self, peer, updates)
        self.iface = iface
        self.command_id = command_id
        self.request_id = request_id
        self.result = result

    def as_dict( self ):
        return dict(ServerNotification.as_dict(self),
                    iface_id=self.iface.iface_id,
                    command=self.command_id,
                    request_id=self.request_id,
                    result=self.result,
                    updates=self.updates,
                    )

    def pprint( self ):
        pprint.pprint(self.as_dict())

    def encode( self, encoder ):
        return encoder.encode(self.get_packet_type(), self)

    def get_packet_type( self ):
        return self.iface.get_response_type(self.command_id)


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

    def as_dict( self ):
        return dict(ClientNotification.as_dict(self),
                    request_id=self.request_id)

    def get_packet_type( self ):
        return self.iface.get_request_type(self.command_id)

    def make_response( self, result=None ):
        result_type = self.iface.get_command_result_type(self.command_id)
        result_type.validate(self.iface.iface_id +  '.Request.result', result)
        return Response(self.peer, self.iface, self.command_id, self.request_id, result)

    def make_response_object( self, obj ):
        return self.make_response(obj)

    def make_response_result( self, **kw ):
        return self.make_response(self.iface.make_result(self.command_id, **kw))

    def make_response_update( self, iface, path, diff ):
        response = self.make_response()
        response.add_update(iface.Update(path, diff))
        return response
