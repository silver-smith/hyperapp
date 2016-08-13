from ..util import is_list_inst, dt2local_str
from .htypes import (
    Type,
    tString,
    tInt,
    tBool,
    tDateTime,
    TOptional,
    Field,
    TRecord,
    TList,
    TIndexedList,
    tCommand,
    tResourceId,
    )
from .interface import RequestCmd, OpenCommand, ContentsCommand, tHandle, tObjHandle, Interface


tListHandleBase = tHandle.register('list_handle', base=tObjHandle)

def list_handle_type( id, key_type ):
    fields = [
        Field('resource_id', tResourceId),
        Field('sort_column_id', tString),
        Field('key', TOptional(key_type)),
        ]
    return tHandle.register(id, base=tListHandleBase, fields=fields)

def list_narrower_handle_type( id, key_type ):
    fields = [
        Field('resource_id', tResourceId),
        Field('sort_column_id', tString),
        Field('key', TOptional(key_type)),
        Field('narrow_field_id', tString),
        ]
    return tHandle.register(id, base=tObjHandle, fields=fields)


class ColumnType(object):

    def to_string( self, value ):
        raise NotImplementedError(self.__class__)


class StringColumnType(ColumnType):

    type = tString

    def to_string( self, value ):
        return value


class IntColumnType(ColumnType):

    type = tInt

    def to_string( self, value ):
        return str(value)


class DateTimeColumnType(ColumnType):

    type = tDateTime

    def to_string( self, value ):
        return dt2local_str(value)


stringColumnType = StringColumnType()
intColumnType = IntColumnType()
dateTimeColumnType = DateTimeColumnType()


class Column(object):

    def __init__( self, id, type=stringColumnType ):
        assert isinstance(id, str), repr(id)
        assert isinstance(type, ColumnType), repr(type)
        self.id = id
        self.type = type

    def __eq__( self, other ):
        assert isinstance(other, Column), repr(other)
        return (other.id == self.id and
                other.type == self.type)


class ElementCommand(RequestCmd):
    pass


class ElementOpenCommand(OpenCommand, ElementCommand):
    pass


class ListInterface(Interface):
        
    def __init__( self, iface_id, base=None, contents_fields=None, commands=None, columns=None, key_column='key' ):
        assert is_list_inst(columns, Column), repr(columns)
        assert isinstance(key_column, str), repr(key_column)
        self.columns = columns
        self.key_column = key_column
        self.key_type = self._pick_key_column().type.type  # used by parent __init__
        self.tRowRecord = TRecord([Field(column.id, column.type.type) for column in columns])  # --//--
        self._tElement = TRecord([
            Field('row', self.tRowRecord),
            Field('commands', TList(tCommand)),
            ])
        self._tDiff = TRecord([
            Field('start_key', self.key_type),          # replace elements from this one
            Field('end_key', self.key_type),            # up to (and including) this one
            Field('elements', TList(self._tElement)),  # with these elemenents
            ])
        self._tSlice = TRecord([
            Field('sort_column_id', tString),
            Field('from_key', TOptional(self.key_type)),
            Field('direction', tString),  # asc/desc; todo: enum
            Field('elements', TList(self._tElement)),
            Field('bof', tBool),
            Field('eof', tBool),
            ])
        commands = [self._resolve_command(command) for command in commands or []]
        Interface.__init__(self, iface_id, base, contents_fields, self._tDiff, commands)

    def __eq__( self, other ):
        return (isinstance(other, ListInterface) and
                Interface.__eq__(self, other) and
                other.columns == self.columns and
                other.key_type == self.key_type and
                other.key_column == self.key_column)

    def _pick_key_column( self ):
        for column in self.columns:
            if column.id == self.key_column:
                return column
        assert False, repr((self.key_column, [column.id for column in self.columns]))  # unknown key column

    def _register_types( self ):
        Interface._register_types(self)
        self._tListHandle = list_handle_type('%s.list' % self.iface_id, self.key_type)
        self._tListNarrowerHandle = list_narrower_handle_type('%s.list_narrower' % self.iface_id, self.key_type)

    def _resolve_command( self, command ):
        if isinstance(command, ElementCommand):
            params_fields = [Field('element_key', self.key_type)] + (command.params_fields or [])
            return RequestCmd(command.command_id, params_fields, command.result_fields)
        else:
            return command

    def get_default_contents_fields( self ):
        return Interface.get_default_contents_fields(self) + [
            Field('slice', self.tSlice()),
            ]

    def get_basic_commands( self ):
        fetch_params_fields = [
            Field('sort_column_id', tString),
            Field('from_key', TOptional(self.key_type)),
            Field('direction', tString),  # asc/desc; todo: enum
            Field('count', tInt),
            ]
        return Interface.get_basic_commands(self) \
            + [ContentsCommand('fetch_elements', fetch_params_fields),
               ContentsCommand('subscribe_and_fetch_elements', fetch_params_fields)]

    def Row( self, *args, **kw ):
        return self.tRowRecord(*args, **kw)

    def tElement( self ):
        return self._tElement

    def Element( self, row, commands=None ):
        return self.tElement()(row, commands or [])

    def tSlice( self ):
        return self._tSlice

    def Slice( self, *args, **kw ):
        return self.tSlice()(*args, **kw)

    def tDiff( self ):
        return self._tDiff

    def Diff( self, *args, **kw ):
        return self.tDiff()(*args, **kw)

    def tListHandle( self ):
        return self._tListHandle

    def ListHandle( self, *args, **kw ):
        return self.tListHandle()(*args, **kw)

    def ListNarrowerHandle( self, *args, **kw ):
        return self._tListNarrowerHandle(*args, **kw)
