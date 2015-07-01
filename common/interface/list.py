from .. util import is_list_inst
from . types import (
    Type,
    TString,
    TInt,
    TBool,
    TOptional,
    TColumnType,
    Field,
    TRecord,
    TList,
    TIndexedList,
    TRow,
    tCommand,
    )
from . interface import Command, OpenCommand, Object, Interface
from .. request import StrColumnType


tColumn = TRecord([
    Field('id', TString()),
    Field('title', TOptional(TString())),
    Field('type', TColumnType()),
    ])


class Column(tColumn.make_class()):

    def __init__( self, id, title=None, type=StrColumnType() ):
        super(Column, self).__init__(id, title, type)


class ElementCommand(Command):

    def get_params_fields( self, iface ):
        assert isinstance(iface, ListInterface), repr(iface)  # ElementCommands can only be used with ListInterface
        fields = Command.get_params_fields(self, iface)
        return [Field('element_key', iface.key_type)] + fields


class ElementOpenCommand(ElementCommand, OpenCommand):

    get_params_fields = ElementCommand.get_params_fields
    get_result_type = OpenCommand.get_result_type


class ListObject(Object):

    @classmethod
    def Element( cls, *args, **kw ):
        return cls.iface.Element(*args, **kw)

    @classmethod
    def FetchedElements( cls, *args, **kw ):
        return cls.iface.FetchedElements(*args, **kw)


class ListInterface(Interface):
        
    def __init__( self, iface_id, content_fields=None, update_type=None, commands=None, columns=None, key_type=TString() ):
        assert is_list_inst(columns, Type), repr(columns)
        assert isinstance(key_type, Type), repr(key_type)
        self.columns = columns
        self.key_type = key_type
        Interface.__init__(self, iface_id, content_fields, update_type,
                           (commands or []) + self._get_basic_commands(key_type))

    def get_default_content_fields( self ):
        return Interface.get_default_content_fields(self) + [
            Field('columns', TIndexedList(tColumn)),
            Field('elements', TList(self.tElement())),
            Field('has_more', TBool()),
            Field('selected_key', TOptional(self.key_type)),
            ]

    def _get_basic_commands( self, key_type ):
        return [
            Command('get_elements', [Field('count', TInt()),
                                     Field('key', key_type)],
                                    [Field('fetched_elements', self.tFetchedElements())]),
                ]

    def tFetchedElements( self ):
        return TRecord([
            Field('elements', TList(self.tElement())),
            Field('has_more', TBool()),
            ])

    def FetchedElements( self, *args, **kw ):
        return self.tFetchedElements().instantiate(*args, **kw)

    def tElement( self ):
        return TRecord([
            Field('key', self.key_type),
            Field('row', TRow(self.columns)),
            Field('commands', TList(tCommand)),
            ])

    def Element( self, *args, **kw ):
        return self.tElement().instantiate(*args, **kw)
