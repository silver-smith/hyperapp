from ..util import is_list_inst, dt2local_str
from .types import (
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
    )
from .interface import RequestCmd, OpenCommand, tHandle, tObjHandle, Interface


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

    def __init__( self, id, title=None, type=stringColumnType ):
        assert isinstance(id, basestring), repr(id)
        assert title is None or isinstance(title, basestring), repr(title)
        assert isinstance(type, ColumnType), repr(type)
        self.id = id
        self.title = title
        self.type = type


class ElementCommand(RequestCmd):

    def get_params_fields( self, iface ):
        assert isinstance(iface, ListInterface), repr(iface)  # ElementCommands can only be used with ListInterface
        fields = RequestCmd.get_params_fields(self, iface)
        return [Field('element_key', iface.key_type)] + fields


class ElementOpenCommand(ElementCommand, OpenCommand):

    get_params_fields = ElementCommand.get_params_fields
    get_result_type = OpenCommand.get_result_type


class ListInterface(Interface):
        
    def __init__( self, iface_id, base=None, content_fields=None, commands=None, columns=None, key_column='key', required_module_id=None ):
        assert is_list_inst(columns, Column), repr(columns)
        assert isinstance(key_column, basestring), repr(key_column)
        self.columns = columns
        self.key_column = key_column
        self.key_type = self._pick_key_column().type.type  # used by parent __init__
        self.tRowRecord = TRecord([Field(column.id, column.type.type) for column in columns])  # --//--
        Interface.__init__(self, iface_id, base, content_fields, self.tDiff(), commands, required_module_id)

    def _pick_key_column( self ):
        for column in self.columns:
            if column.id == self.key_column:
                return column
        assert False, repr((self.key_column, [column.id for column in self.columns]))  # unknown key column

    def _register_types( self ):
        Interface._register_types(self)
        list_fields = [Field('key', TOptional(self.key_type))]
        narrower_fields = [Field('field_id', tString),
                           Field('key', TOptional(self.key_type))]
        self._tListHandle = tHandle.register(
            '%s.list' % self.iface_id, list_fields, base=tObjHandle)
        self._tListNarrowerHandle = tHandle.register(
            '%s.list_narrower' % self.iface_id, narrower_fields, base=tObjHandle)

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
            + [RequestCmd('fetch_elements', fetch_params_fields, [Field('slice', self.tSlice())]),
               RequestCmd('subscribe_and_fetch_elements', fetch_params_fields, self.get_contents_fields())]

    def Row( self, *args, **kw ):
        return self.tRowRecord.instantiate(*args, **kw)

    def tElement( self ):
        return TRecord([
            Field('row', self.tRowRecord),
            Field('commands', TList(tCommand)),
            ])

    def Element( self, row, commands=None ):
        return self.tElement().instantiate(row, commands or [])

    def tSlice( self ):
        return TRecord([
            Field('sort_column_id', tString),
            Field('from_key', TOptional(self.key_type)),
            Field('direction', tString),  # asc/desc; todo: enum
            Field('elements', TList(self.tElement())),
            Field('bof', tBool),
            Field('eof', tBool),
            ])

    def Slice( self, *args, **kw ):
        return self.tSlice().instantiate(*args, **kw)

    def tDiff( self ):
        return TRecord([
            Field('start_key', self.key_type),          # replace elements from this one
            Field('end_key', self.key_type),            # up to (and including) this one
            Field('elements', TList(self.tElement())),  # with these elemenents
            ])

    def Diff( self, *args, **kw ):
        return self.tDiff().instantiate(*args, **kw)

    def tListHandle( self ):
        return self._tListHandle

    def ListHandle( self, *args, **kw ):
        return self.tListHandle().instantiate(*args, **kw)

    def ListNarrowerHandle( self, *args, **kw ):
        return self._tListNarrowerHandle.instantiate(*args, **kw)
