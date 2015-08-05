from .. util import is_list_inst
from . types import (
    join_path,
    Type,
    TPrimitive,
    tString,
    TOptional,
    Field,
    TRecord,
    TList,
    tPath,
    tCommand,
    )
from dynamic_record import TDynamicRec
from . hierarchy import THierarchy


class TIface(TPrimitive):

    type_name = 'interface'

    def get_type( self ):
        return Interface


# base class for server objects
class Object(object):

    def get( self ):
        raise NotImplementedError(self.__class__)


class TObject(TDynamicRec):

    def __init__( self ):
        TDynamicRec.__init__(self, [
            Field('iface', TIface()),
            Field('path', tPath),
            Field('proxy_id', tString),
            ])

    def resolve_dynamic( self, rec ):
        tContents = rec.iface.tContents()
        return TRecord([Field('contents', tContents)], base=self)

    def validate( self, path, value ):
        if value is None: return  # missing objects are allowed
        self.expect(path, value, 'Object', isinstance(value, Object))


tObject = TObject()

tHandle = THierarchy()
tObjHandle = tHandle.register('obj_handle', fields=[Field('object', tObject)])
ObjHandle = tObjHandle.instantiate


class IfaceCommand(object):

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


class RequestCmd(IfaceCommand):
    pass

class NotificationCmd(IfaceCommand):
    pass


class OpenCommand(RequestCmd):

    def get_result_type( self, iface ):
        return tHandle


class SubscribeCommand(RequestCmd):

    def __init__( self ):
        RequestCmd.__init__(self, 'subscribe')

    def get_result_type( self, iface ):
        return iface.tContents()


class Interface(object):

    # client request types
    rt_request = 1
    rt_notification =2

    def __init__( self, iface_id, base=None, content_fields=None, diff_type=None, commands=None ):
        assert base is None or isinstance(base, Interface), repr(base)
        assert is_list_inst(content_fields or [], Field), repr(content_fields)
        assert diff_type is None or isinstance(diff_type, Type), repr(diff_type)
        assert is_list_inst(commands or [], (RequestCmd, NotificationCmd)), repr(commands)
        self.iface_id = iface_id
        self.content_fields = content_fields or []
        self.diff_type = diff_type
        self.commands = commands or []
        if base:
            self.content_fields = base.content_fields + self.content_fields
            self.commands = base.commands + self.commands
            assert diff_type is None, repr(diff_type)  # Inherited from base
            self.diff_type = base.diff_type
        self.id2command = dict((cmd.command_id, cmd) for cmd in self.commands + self.get_basic_commands())

    def get_basic_commands( self ):
        return [
            OpenCommand('get'),
            SubscribeCommand(),
            NotificationCmd('unsubscribe'),
            ]

    def get_request_type( self, command_id ):
        assert command_id in self.id2command, repr(command_id)  # Unknown command id
        command = self.id2command[command_id]
        if isinstance(command, RequestCmd):
            return self.rt_request
        if isinstance(command, NotificationCmd):
            return self.rt_notification
        assert False, command_id  # Only RequestCmd or NotificationCmd are expected here

    def is_open_command( self, command_id ):
        return isinstance(self.id2command[command_id], OpenCommand)

    def get_request_params_type( self, command_id ):
        assert command_id in self.id2command, repr(command_id)  # Unknown command
        return self.id2command[command_id].get_params_type(self)

    def make_params( self, command_id, *args, **kw ):
        return self.get_request_params_type(command_id).instantiate(*args, **kw)

    def get_command_result_type( self, command_id ):
        return self.id2command[command_id].get_result_type(self)

    def make_result( self, command_id, *args, **kw ):
        return self.get_command_result_type(command_id).instantiate(*args, **kw)

    def validate_request( self, command_id, params=None ):
        cmd = self.id2command.get(command_id)
        if not cmd:
            raise TypeError('%s: Unsupported command id: %r' % (self.iface_id, command_id))
        cmd.get_params_type(self).validate(join_path(self.iface_id, command_id, 'params'), params)

    def Object( self, **kw ):
        return tObject.instantiate(**kw)

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

    def Update( self, path, diff ):
        return tUpdate.instantiate(self, path, diff)


class TUpdate(TDynamicRec):

    def __init__( self ):
        fields = [
            Field('iface', TIface()),
            Field('path', tPath),
            ]
        TDynamicRec.__init__(self, fields)

    def resolve_dynamic( self, rec ):
        diff_type = rec.iface.get_diff_type()
        return TRecord([Field('diff', diff_type)], base=self)


tUpdate = TUpdate()
tUpdateList = TList(tUpdate)


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
