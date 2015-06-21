import pprint
from . util import is_list_inst


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


class Column(object):

    def __init__( self, id, title=None, type=StrColumnType() ):
        assert isinstance(type, ColumnType), repr(type)
        self.id = id
        self.title = title
        self.type = type

    def as_json( self ):
        return dict(
            id=self.id,
            title=self.title,
            type=self.type.id
            )

    @classmethod
    def column_from_json( cls, idx, data ):
        ts = data.type
        if ts == 'str':
            t = StrColumnType()
        elif ts == 'datetime':
            t = DateTimeColumnType()
        else:
            assert False, repr(t)  # Unknown column type
        return cls(idx, data.id, data.title, t)


class Element(object):

    def __init__( self, key, row, commands=None ):
        self.key = key
        self.row = row  # value list
        self.commands = commands or []

    def as_json( self ):
        return dict(
            key=self.key,
            row=self.row,
            commands=[cmd.as_json() for cmd in self.commands],
            )

    @classmethod
    def from_json( cls, data ):
        key = data.key
        row = data.row
        return cls(key, row, [Command.from_json(cmd) for cmd in data.commands])


class Command(object):

    def __init__( self, id, text, desc, shortcut=None ):
        assert shortcut is None or isinstance(shortcut, basestring) or is_list_inst(shortcut, basestring), repr(shortcut)
        self.id = id
        self.text = text
        self.desc = desc
        self.shortcut = shortcut

    def as_json( self ):
        return dict(
            id=self.id,
            text=self.text,
            desc=self.desc,
            shortcut=self.shortcut,
            )

    @classmethod
    def from_json( cls, data ):
        return cls(data.id, data.text, data.desc, data.shortcut)


class Diff(object):
    pass


class ListDiff(Diff):

    @classmethod
    def add_one( cls, key, element ):
        return cls(key, key, [element])

    @classmethod
    def add_many( cls, key, elements ):
        return cls(key, key, elements)

    @classmethod
    def append_many( cls, key, elements ):
        return cls.add_many(None, elements)

    @classmethod
    def delete( cls, key ):
        return cls(key, key, [])

    def __init__( self, start_key, end_key, elements ):
        # keys == None means append
        self.start_key = start_key  # replace elements from this one
        self.end_key = end_key      # up to (and including) this one
        self.elements = elements    # with these elemenents

    def as_json( self ):
        return dict(
            start_key=self.start_key,
            end_key=self.end_key,
            elements=[elt.as_json() for elt in self.elements])

    @classmethod
    def from_json( cls, data ):
        return cls(
            start_key=data['start_key'],
            end_key=data['end_key'],
            elements=[Element.from_json(elt) for elt in data['elements']],
            )


class ServerNotification(object):

    def __init__( self, peer, updates=None ):
        self.peer = peer
        self.updates = updates or []  # (path, ListDiff) list

    def add_update( self, path, diff ):
        self.updates.append((path, diff))

    def as_json( self ):
        d = dict()
        if self.updates:
            d['updates'] = [(path, diff.as_json()) for path, diff in self.updates]
        return d


class Response(ServerNotification):

    def __init__( self, peer, iface, command_id, request_id, result_dict=None, result=None, updates=None ):
        ServerNotification.__init__(self, peer, updates)
        self.iface = iface
        self.command_id = command_id
        self.request_id = request_id
        self.result_dict = result_dict
        self.result = result

    def as_json( self ):
        return dict(ServerNotification.as_json(self),
                    iface_id=self.iface.iface_id,
                    command=self.command_id,
                    request_id=self.request_id,
                    result=self.result_dict,
                    )

    def pprint( self ):
        pprint.pprint(self.as_json())

    def encode( self, encoder ):
        return encoder.encode(self.get_packet_type(), self.as_json())

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
        return encoder.encode(self.get_packet_type(), self.as_dict())

    def as_dict( self ):
        return dict(
            iface_id=self.iface.iface_id,
            path=self.path,
            command=self.command_id,
            params=self.params)

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

    def make_response( self, result_dict=None ):
        return Response(self.peer, self.iface, self.command_id, self.request_id, result_dict)

    def make_response_object( self, obj ):
        self.iface.validate_result(self.command_id, obj)
        return self.make_response(obj)

    def make_response_result( self, **kw ):
        self.iface.validate_result(self.command_id, kw)
        return self.make_response(kw)

    def make_response_update( self, path, diff ):
        assert isinstance(diff, ListDiff), repr(diff)
        response = self.make_response()
        response.add_update(path, diff)
        return response
