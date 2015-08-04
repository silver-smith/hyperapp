from .. util import is_list_inst, dt2local_str
from . types import (
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
from . hierarchy import THierarchy
from . interface import RequestCmd, OpenCommand, tHandle, tObjHandle, Object, Interface


tListHandleBase = tHandle.register('list_base', base=tObjHandle)
tListNarrowerHandleBase = tHandle.register('list_narrower_base', base=tObjHandle)

tColumnType = THierarchy()


class ColumnType(object):

    def to_string( self, value ):
        raise NotImplementedError(self.__class__)


class StrColumnType(ColumnType):

    type = tString

    def to_string( self, value ):
        return value


class DateTimeColumnType(ColumnType):

    type = tDateTime

    def to_string( self, value ):
        return dt2local_str(value)


tColumnType.register('str', cls=StrColumnType)
tColumnType.register('datetime', cls=DateTimeColumnType)


class Column(object):

    def __init__( self, id, title=None, type=StrColumnType() ):
        assert isinstance(id, basestring), repr(id)
        assert isinstance(title, basestring), repr(title)
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


class ListObject(Object):

    @classmethod
    def Element( cls, *args, **kw ):
        return cls.iface.Element(*args, **kw)

    @classmethod
    def Diff( cls, *args, **kw ):
        return cls.iface.Diff(*args, **kw)

    @classmethod
    def Diff_insert_one( cls, key, element ):
        return cls.Diff_insert_many(key, [element])

    @classmethod
    def Diff_insert_many( cls, key, elements ):
        return cls.Diff(key, key, elements)

    @classmethod
    def Diff_append_many( cls, elements ):
        return cls.Diff.insert_many(None, elements)

    @classmethod
    def Diff_delete( cls, key ):
        return cls.Diff(key, key, [])

    @classmethod
    def ListHandle( cls, *args, **kw ):
        return cls.iface.ListHandle(*args, **kw)

    @classmethod
    def ListNarrowerHandle( cls, *args, **kw ):
        return cls.iface.ListNarrowerHandle(*args, **kw)


class ListInterface(Interface):
        
    def __init__( self, iface_id, base=None, content_fields=None, commands=None, columns=None, key_column='key' ):
        assert is_list_inst(columns, Column), repr(columns)
        assert isinstance(key_column, basestring), repr(key_column)
        self.columns = columns
        self.key_column = key_column
        Interface.__init__(self, iface_id, base, content_fields, self.tDiff(), commands)
        self.tRowRecord = TRecord([Field(column.id, column.type.type) for column in columns])
        self.key_type = self._pick_key_column().type.type
        self._register_types()

    def _pick_key_column( self ):
        for column in self.columns:
            if column.id == self.key_column:
                return column
        assert False, repr((self.key_column, [column.id for column in self.columns]))  # unknown key column

    def _register_types( self ):
        fields = [Field('key', TOptional(self.key_type))]
        self._tListHandle = tHandle.register(
            '%s.list' % self.iface_id, fields, base=tListHandleBase)
        self._tListNarrowerHandle = tHandle.register(
            '%s.list_narrower' % self.iface_id, fields, base=tListNarrowerHandleBase)

    def get_default_content_fields( self ):
        return Interface.get_default_content_fields(self) + [
            Field('sorted_by_column', tString),
            Field('elements', TList(self.tElement())),
            Field('eof', tBool),
            ]

    def get_basic_commands( self ):
        return Interface.get_basic_commands(self) \
            + [RequestCmd('fetch_elements',
                          [Field('sort_by_column', tString),
                           Field('key', self.key_type),
                           Field('desc_count', tInt),
                           Field('asc_count', tInt)],
                          [Field('elements', TList(self.tElement())),
                           Field('eof', tBool)])]

    def Row( self, *args, **kw ):
        return self.tRowRecord.instantiate(*args, **kw)

    def tElement( self ):
        return TRecord([
            Field('row', self.tRowRecord),
            Field('commands', TList(tCommand)),
            ])

    def Element( self, row, commands=None ):
        return self.tElement().instantiate(row, commands or [])

    def tDiff( self ):
        return TRecord([
            Field('start_key', self.key_type),          # replace elements from this one
            Field('end_key', self.key_type),            # up to (and including) this one
            Field('elements', TList(self.tElement())),  # with these elemenents
            ])

    def Diff( self, *args, **kw ):
        return self.tDiff().instantiate(*args, **kw)

    def ListHandle( self, *args, **kw ):
        return self._tListHandle.instantiate(*args, **kw)

    def ListNarrowerHandle( self, *args, **kw ):
        return self._tListNarrowerHandle.instantiate(*args, **kw)
