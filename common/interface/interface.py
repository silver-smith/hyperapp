from .. util import is_list_inst
from . types import (
    join_path,
    Type,
    TPrimitive,
    TString,
    TInt,
    TBool,
    TColumnType,
    TOptional,
    Field,
    TRecord,
    TList,
    TIndexedList,
    TRow,
    TPath,
    TUpdate,
    TObject,
    )
from .. request import ClientNotification, Request


class TClientNotification(TPrimitive):
    type_name = 'client_notification'
    type = ClientNotification

class TRequest(TPrimitive):
    type_name = 'request'
    type = Request


class Command(object):

    def __init__( self, command_id, params_fields=None, result_fields=None ):
        self.command_id = command_id
        self.params_fields = params_fields or []
        self.result_fields = result_fields or []

    def get_params_type( self, iface ):
        return TRecord(self.get_params_fields(iface))

    def get_result_type( self, iface ):
        return TRecord(self.get_result_fields(iface))

    def get_params_fields( self, iface ):
        return self.params_fields

    def get_result_fields( self, iface ):
        return self.result_fields

    def validate_request( self, iface, path, params_dict ):
        self._validate_record('params', self.get_params_type(iface), path, params_dict)

    def validate_result( self, iface, path, result_dict ):
        self._validate_record('result', self.get_result_type(iface), path, result_dict)

    def _validate_record( self, rec_name, type, path, rec_dict ):
        rec_path = join_path(path, self.command_id, rec_name)
        type.validate(rec_path, rec_dict)


class OpenCommand(Command):

    def get_result_type( self, iface ):
        return TObject()


class SubscribeCommand(Command):

    def __init__( self ):
        Command.__init__(self, 'subscribe')

    def get_result_type( self, iface ):
        return iface.get_contents_type()


class Interface(object):

    basic_commands = [
        OpenCommand('get'),
        SubscribeCommand(),
        Command('unsubscribe'),
        ]

    def __init__( self, iface_id, content_fields=None, update_type=None, commands=None ):
        assert is_list_inst(content_fields or [], Field), repr(content_fields)
        assert update_type is None or isinstance(update_type, Type), repr(update_type)
        assert is_list_inst(commands or [], Command), repr(commands)
        self.iface_id = iface_id
        self.content_fields = content_fields or []
        self.update_type = update_type
        self.commands = dict((cmd.command_id, cmd) for cmd in (commands or []) + self.basic_commands)

    def get_request_type( self, command_id ):
        params_type = self.get_command_params_type(command_id)
        return TRecord([
            Field('iface_id', TString()),
            Field('path', TPath()),
            Field('command', TString()),
            Field('request_id', TString()),
            Field('params', params_type),
            ])

    def get_client_notification_type( self ):
        params_type = self.get_command_params_type(command_id)
        return TRecord([
            Field('iface_id', TString()),
            Field('path', TPath()),
            Field('command', TString()),
            Field('params', params_type),
            ])

    def get_response_type( self, command_id ):
        result_type = self.get_command_result_type(command_id)
        return TRecord([
            Field('iface_id', TString()),
            Field('command', TString()),
            Field('request_id', TString()),
            Field('result', result_type),
            Field('updates', self.get_updates_type()),
            ])

    def get_updates_type( self ):
        return TList(TUpdate())

    def is_open_command( self, command_id ):
        return isinstance(self.commands[command_id], OpenCommand)

    def get_command_params_type( self, command_id ):
        return self.commands[command_id].get_params_type(self)

    def get_command_result_type( self, command_id ):
        return self.commands[command_id].get_result_type(self)

    def get_command_params_fields( self, command_id ):
        return self.commands[command_id].get_params_fields(self)

    def validate_request( self, command_id, args=None ):
        cmd = self.commands.get(command_id)
        if not cmd:
            raise TypeError('%s: Unsupported command id: %r' % (self.iface_id, command_id))
        cmd.validate_request(self, self.iface_id, args or {})

    def validate_result( self, command_id, rec ):
        cmd = self.commands.get(command_id)
        if not cmd:
            raise TypeError('%s: Unsupported command id: %r' % (self.iface_id, command_id))
        cmd.validate_result(self, self.iface_id, rec)

    def validate_contents( self, path, value ):
        self.get_contents_type().validate(path, value)

    def validate_update_diff( self, diff ):
        assert self.update_type, 'No update type is defined for %r interface' % self.iface_id
        self.update_type.validate('diff', diff)

    def get_type( self ):
        return TRecord([
            Field('iface_id', TString()),
            Field('proxy_id', TString()),
            Field('view_id', TString()),
            Field('path', TPath()),
            Field('contents', self.get_contents_type()),
            ])

    def get_contents_type( self ):
        return TRecord(self.get_default_content_fields() + self.content_fields)

    def get_default_content_fields( self ):
        return [Field('commands', TList(self._get_command_type()))]

    def get_update_type( self ):
        return self.update_type

    def _get_command_type( self ):
        return TRecord([
            Field('id', TString()),
            Field('text', TString()),
            Field('desc', TString()),
            Field('shortcut', TOptional(TString())),
            ])


class ElementCommand(Command):

    def get_params_fields( self, iface ):
        assert isinstance(iface, ListInterface), repr(iface)  # ElementCommands can only be used with ListInterface
        fields = Command.get_params_fields(self, iface)
        return [Field('element_key', iface.key_type)] + fields


class ElementOpenCommand(ElementCommand, OpenCommand):

    get_params_fields = ElementCommand.get_params_fields
    get_result_type = OpenCommand.get_result_type


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
            Field('columns', TIndexedList(self._get_column_type())),
            Field('elements', TList(self._get_element_type())),
            Field('has_more', TBool()),
            Field('selected_key', TOptional(self.key_type)),
            ]

    def _get_column_type( self ):
        return TRecord([
            Field('id', TString()),
            Field('type', TColumnType()),
            Field('title', TOptional(TString())),
            ])

    def _get_basic_commands( self, key_type ):
        return [
            Command('get_elements', [Field('count', TInt()),
                                     Field('key', key_type)],
                                    [Field('fetched_elements', self._get_fetched_elements_type())]),
                ]

    def _get_fetched_elements_type( self ):
        return TRecord([
            Field('elements', TList(self._get_element_type())),
            Field('has_more', TBool()),
            ])

    def _get_element_type( self ):
        return TRecord([
            Field('commands', TList(self._get_command_type())),
            Field('key', self.key_type),
            Field('row', TRow(self.columns)),
            ])


class IfaceRegistry(object):

    def __init__( self ):
        self.registry = {}  # iface id -> Interface

    def register( self, iface ):
        assert isinstance(iface, Interface), repr(iface)
        self.registry[iface.iface_id] = iface

    def resolve( self, iface_id ):
        return self.registry[iface_id]


iface_registry = IfaceRegistry()

def register_iface( iface ):
    iface_registry.register(iface)

def resolve_iface( iface_id ):
    return iface_registry.resolve(iface_id)
