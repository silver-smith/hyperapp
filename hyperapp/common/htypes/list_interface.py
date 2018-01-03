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
    )
from .hierarchy import THierarchy
from .meta_type import tMetaType, tInterfaceMeta, t_named, field_list_from_data, command_from_data
from .interface import RequestCmd, ContentsCommand, Interface


def categorized_list_handle_type(core_types, key_t):
    if key_t is tString:
        return core_types.categorized_string_list_handle
    if key_t is tInt:
        return core_types.categorized_int_list_handle
    assert False, 'Unsupported list key type: %r' % key_t

def list_handle_type(core_types, key_t):
    if key_t is tString:
        return core_types.string_list_handle
    if key_t is tInt:
        return core_types.int_list_handle
    assert False, 'Unsupported list key type: %r' % key_t


class Column(object):

    @classmethod
    def from_data(cls, meta_type_registry, type_registry, rec):
        t = meta_type_registry.resolve(type_registry, rec.type)
        return cls(rec.id, t, rec.is_key)

    def __init__(self, id, type=tString, is_key=False):
        assert isinstance(id, str), repr(id)
        assert isinstance(type, Type), repr(type)
        assert isinstance(is_key, bool), repr(is_key)
        self.id = id
        self.type = type
        self.is_key = is_key

    def __eq__(self, other):
        assert isinstance(other, Column), repr(other)
        return (other.id == self.id and
                other.type == self.type and
                other.is_key == self.is_key)

    def __hash__(self):
        return hash((self.id, self.type, self.is_key))


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


def t_column_meta(id, type, is_key):
    return tColumn(id, type, is_key)

def t_list_interface_meta(iface_id, base_iface_id, commands, columns, contents_fields=None, diff_type=None):
    return tListInterface(tListInterface.id, iface_id, base_iface_id, contents_fields or [], diff_type, commands, columns)

def list_interface_from_data(meta_type_registry, type_registry, rec):
    contents_fields = field_list_from_data(meta_type_registry, type_registry, rec.contents_fields)
    assert rec.diff_type is None, repr(rec.diff_type)  # list interface makes it's own diff type
    commands = [command_from_data(meta_type_registry, type_registry, command) for command in rec.commands]
    columns = [Column.from_data(meta_type_registry, type_registry, column) for column in rec.columns]
    return ListInterface(rec.iface_id, contents_fields=contents_fields, commands=commands, columns=columns)


stringColumnType = tSimpleColumnType('string')
intColumnType = tSimpleColumnType('int')
dateTimeColumnType = tSimpleColumnType('date_time')


def row_type(column_list):
    assert is_list_inst(column_list, Column), repr(column_list)
    return TRecord([Field(column.id, column.type) for column in column_list])

def element_type(row_t):
    return TRecord([
        Field('row', row_t),
        Field('commands', TList(tString)),
        ])

def diff_type(key_t, element_t):
    return TRecord([
        Field('remove_keys', TList(key_t)),
        Field('elements', TList(element_t)),
        ])

def chunk_type(key_t, element_t):
    return TRecord([
        Field('sort_column_id', tString),
        Field('from_key', TOptional(key_t)),
        Field('elements', TList(element_t)),
        Field('bof', tBool),
        Field('eof', tBool),
        ])


class ElementCommand(RequestCmd):
    pass


class ListInterface(Interface):
    
    def __init__(self, iface_id, base=None, contents_fields=None, commands=None, columns=None):
        assert is_list_inst(columns, Column), repr(columns)
        self._id2column = dict((column.id, column) for column in columns)
        self._columns = columns
        self._key_column_id = self._pick_key_column_id()
        self._key_type = self._id2column[self._key_column_id].type
        self._row_t = row_type(columns)
        self._element_t = element_type(self._row_t)
        self._diff_t = diff_type(self._key_type, self._element_t)
        self._chunk_t = chunk_type(self._key_type, self._element_t)
        Interface.__init__(self, iface_id, base, contents_fields, self._diff_t, commands)

    def __eq__(self, other):
        return (isinstance(other, ListInterface) and
                Interface.__eq__(self, other) and
                other._columns == self._columns and
                other._key_column_id == self._key_column_id)

    def __hash__(self):
        return hash((
            tuple(self._columns),
            self._key_column_id,
            ))

    def _pick_key_column_id(self):
        key_column_id = None
        for column in self._columns:
            if column.is_key:
                assert not key_column_id, 'Only one key column is supported, but got two: %r and %r' % (key_column_id, column.id)
                key_column_id = column.id
        assert key_column_id, 'No column with is_key is found'
        return key_column_id

    def _resolve_and_bind_command(self, command, params_fields=None, result_fields=None, result_type=None):
        if isinstance(command, ElementCommand):
            params_fields = [Field('element_key', self._key_type)] + (params_fields or command.params_fields or [])
        return Interface._resolve_and_bind_command(self, command, params_fields, result_fields, result_type)

    def get_key_type(self):
        return self._key_type

    def get_columns(self):
        return self._columns

    def get_key_column_id(self):
        return self._key_column_id

    def get_default_contents_fields(self):
        return Interface.get_default_contents_fields(self) + [
            Field('chunk', self.Chunk),
            ]

    def get_basic_commands(self, core_types):
        fetch_params_fields = [
            Field('sort_column_id', tString),
            Field('from_key', TOptional(self._key_type)),
            Field('desc_count', tInt),
            Field('asc_count', tInt),
            ]
        return Interface.get_basic_commands(self, core_types) \
            + [ContentsCommand('fetch_elements', fetch_params_fields),
               ContentsCommand('subscribe_and_fetch_elements', fetch_params_fields)]

    @property
    def Row(self):
        return self._row_t

    @property
    def Element(self):
        return self._element_t

    @property
    def Chunk(self):
        return self._chunk_t

    @property
    def Diff(self):
        return self._diff_t
