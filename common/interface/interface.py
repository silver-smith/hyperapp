from .. util import is_list_inst
from . types import (
    join_path,
    Type,
    TPrimitive,
    TString,
    TOptional,
    Field,
    TRecord,
    TList,
    TPath,
    tCommand,
    )
from .. request import ClientNotification, Request


class TUpdate(Type):

    def __init__( self ):
        self.info_type = TRecord([
            Field('iface', TIface()),
            Field('path', TPath()),
            ])


# base class for server objects
class Object(object):

    def get( self ):
        raise NotImplementedError(self.__class__)


class TObject(TRecord):

    def __init__( self ):
        TRecord.__init__(self, [
            Field('iface', TIface()),
            Field('path', TPath()),
            Field('proxy_id', TString()),
            Field('view_id', TString()),
            Field('contents', None),
            ])

    def validate( self, path, value ):
        if value is None: return  # missing objects are allowed
        self.expect(path, value, 'Object', isinstance(value, Object))


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

    def validate_request( self, iface, path, params_kw ):
        self._validate_record('params', self.get_params_type(iface), path, params_kw)

    def validate_result( self, iface, path, result_kw ):
        self._validate_record('result', self.get_result_type(iface), path, result_kw)

    def _validate_record( self, rec_name, type, path, rec_kw ):
        rec_path = join_path(path, self.command_id, rec_name)
        type.validate_kw(rec_path, rec_kw)


class OpenCommand(Command):

    def get_result_type( self, iface ):
        return TObject()


class SubscribeCommand(Command):

    def __init__( self ):
        Command.__init__(self, 'subscribe')

    def get_result_type( self, iface ):
        return iface.tContents()


class Interface(object):

    basic_commands = [
        OpenCommand('get'),
        SubscribeCommand(),
        Command('unsubscribe'),
        ]

    def __init__( self, iface_id, content_fields=None, diff_type=None, commands=None ):
        assert is_list_inst(content_fields or [], Field), repr(content_fields)
        assert diff_type is None or isinstance(diff_type, Type), repr(diff_type)
        assert is_list_inst(commands or [], Command), repr(commands)
        self.iface_id = iface_id
        self.content_fields = content_fields or []
        self.diff_type = diff_type
        self.commands = dict((cmd.command_id, cmd) for cmd in (commands or []) + self.basic_commands)

    def get_request_type( self, command_id ):
        params_type = self.get_command_params_type(command_id)
        return TRecord([
            Field('iface', TIface()),
            Field('path', TPath()),
            Field('command_id', TString()),
            Field('request_id', TString()),
            Field('params', params_type),
            ])

    def get_client_notification_type( self ):
        params_type = self.get_command_params_type(command_id)
        return TRecord([
            Field('iface', TIface()),
            Field('path', TPath()),
            Field('command', TString()),
            Field('params', params_type),
            ])

    def get_response_type( self, command_id ):
        result_type = self.get_command_result_type(command_id)
        return TRecord([
            Field('iface', TIface()),
            Field('command_id', TString()),
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

    def make_params( self, command_id, **kw ):
        return self.get_command_params_type(command_id).instantiate(**kw)

    def get_command_result_type( self, command_id ):
        return self.commands[command_id].get_result_type(self)

    def make_result( self, command_id, **kw ):
        return self.get_command_result_type(command_id).instantiate(**kw)

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

    def validate_update_diff( self, diff ):
        assert self.diff_type, 'No diff type is defined for %r interface' % self.iface_id
        self.diff_type.validate('diff', diff)

    def get_type( self ):
        return TRecord([
            Field('iface', TIface()),
            Field('proxy_id', TString()),
            Field('view_id', TString()),
            Field('path', TPath()),
            Field('contents', self.tContents()),
            ])

    def Object( self, **kw ):
        return self.get_type().instantiate(**kw)

    def get_default_content_fields( self ):
        return [Field('commands', TList(tCommand))]

    def tContents( self ):
        return TRecord(self.get_default_content_fields() + self.content_fields)

    def Contents( self, **kw ):
        return self.tContents().instantiate(**kw)
        
    def validate_contents( self, path, value ):
        self.tContents().validate(path, value)

    def get_diff_type( self ):
        return self.diff_type


class TIface(TPrimitive):
    type_name = 'interface'
    type = Interface


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
