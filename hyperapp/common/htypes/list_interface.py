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
from .hierarchy import THierarchy
from .meta_type import tMetaType, tInterfaceMeta, t_named, field_list_from_data, command_from_data
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


class Column(object):

    @classmethod
    def from_data( cls, meta_registry, type_registry, rec ):
        t = meta_registry.resolve(type_registry, rec.type)
        return cls(rec.id, t, rec.is_key)

    def __init__( self, id, type=tString, is_key=False ):
        assert isinstance(id, str), repr(id)
        assert isinstance(type, Type), repr(type)
        assert isinstance(is_key, bool), repr(is_key)
        self.id = id
        self.type = type
        self.is_key = is_key

    def __eq__( self, other ):
        assert isinstance(other, Column), repr(other)
        return (other.id == self.id and
                other.type == self.type and
                other.is_key == self.is_key)


tColumn = TRecord([
    Field('id', tString),
    Field('type', tMetaType),
    Field('is_key', tBool),
    ])

tColumnType = THierarchy('column_type')
tSimpleColumnType = tColumnType.register('simple', fields=[Field('impl_id', tString)])

tListInterface = tMetaType.register('list_interface', base=tInterfaceMeta, fields=[
    Field('columns', TList(tColumn)),
    ])


def t_column_meta( id, type, is_key ):
    return tColumn(id, type, is_key)

def t_list_interface_meta( iface_id, base_iface_id, commands, columns, contents_fields=None, diff_type=None ):
    return tListInterface(tListInterface.id, iface_id, base_iface_id, contents_fields or [], diff_type, commands, columns)

def list_interface_from_data( meta_registry, type_registry, rec ):
    contents_fields = field_list_from_data(meta_registry, type_registry, rec.contents_fields)
    assert rec.diff_type is None, repr(rec.diff_type)  # list interface makes it's own diff type
    commands = [command_from_data(meta_registry, type_registry, command) for command in rec.commands]
    columns = [Column.from_data(meta_registry, type_registry, column) for column in rec.columns]
    return ListInterface(rec.iface_id, contents_fields=contents_fields, commands=commands, columns=columns)


stringColumnType = tSimpleColumnType('string')
intColumnType = tSimpleColumnType('int')
dateTimeColumnType = tSimpleColumnType('date_time')


class ElementCommand(RequestCmd):
    pass


class ElementOpenCommand(OpenCommand, ElementCommand):
    pass


class ListInterface(Interface):
        
    def __init__( self, iface_id, base=None, contents_fields=None, commands=None, columns=None ):
        assert is_list_inst(columns, Column), repr(columns)
        self._id2column = dict((column.id, column) for column in columns)
        self._columns = columns
        self._key_column_id = self._pick_key_column_id()
        self._key_type = self._id2column[self._key_column_id].type
        self._tRowRecord = TRecord([Field(column.id, column.type) for column in columns])
        self._tElement = TRecord([
            Field('row', self._tRowRecord),
            Field('commands', TList(tCommand)),
            ])
        self._tDiff = TRecord([
            Field('start_key', self._key_type),          # replace elements from this one
            Field('end_key', self._key_type),            # up to (and including) this one
            Field('elements', TList(self._tElement)),  # with these elemenents
            ])
        self._tSlice = TRecord([
            Field('sort_column_id', tString),
            Field('from_key', TOptional(self._key_type)),
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
                other._columns == self._columns and
                other._key_column_id == self._key_column_id)

    def _pick_key_column_id( self ):
        key_column_id = None
        for column in self._columns:
            if column.is_key:
                assert not key_column_id, 'Only one key column is supported, but got two: %r and %r' % (key_column_id, column.id)
                key_column_id = column.id
        assert key_column_id, 'No column with is_key is found'
        return key_column_id

    def register_types( self ):
        Interface.register_types(self)
        self._tListHandle = list_handle_type('%s.list' % self.iface_id, self._key_type)
        self._tListNarrowerHandle = list_narrower_handle_type('%s.list_narrower' % self.iface_id, self._key_type)

    def _resolve_command( self, command ):
        if isinstance(command, ElementCommand):
            params_fields = [Field('element_key', self._key_type)] + (command.params_fields or [])
            return RequestCmd(command.command_id, params_fields, command.result_fields)
        else:
            return command

    def get_columns( self ):
        return self._columns

    def get_key_column_id( self ):
        return self._key_column_id

    def get_default_contents_fields( self ):
        return Interface.get_default_contents_fields(self) + [
            Field('slice', self.tSlice()),
            ]

    def get_basic_commands( self ):
        fetch_params_fields = [
            Field('sort_column_id', tString),
            Field('from_key', TOptional(self._key_type)),
            Field('direction', tString),  # asc/desc; todo: enum
            Field('count', tInt),
            ]
        return Interface.get_basic_commands(self) \
            + [ContentsCommand('fetch_elements', fetch_params_fields),
               ContentsCommand('subscribe_and_fetch_elements', fetch_params_fields)]

    def Row( self, *args, **kw ):
        return self._tRowRecord(*args, **kw)

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
