from ..util import is_list_inst
from .htypes import (
    join_path,
    Type,
    tNone,
    tString,
    TOptional,
    Field,
    TRecord,
    TList,
    tEndpoint,
    tPath,
    tUrl,
    tIfaceId,
    tCommand,
    )
from .hierarchy import THierarchy
from .request import tUpdate, tClientNotificationRec, tResponseRec


tObject = THierarchy('object')
tBaseObject = tObject.register('object', fields=[Field('objimpl_id', tString)])

# proxy to server returning this object
tThisProxyObject = tObject.register('this_proxy', base=tBaseObject, fields=[
    Field('iface', tIfaceId),
    Field('path', tPath),
    ])

# proxy to server with this endpoint
tProxyObject = tObject.register('proxy', base=tThisProxyObject, fields=[
    Field('endpoint', tEndpoint),
    ])

# base for server response objects
tThisProxyObjectWithContents = tObject.register('this_proxy_with_contents', base=tThisProxyObject)


tHandle = THierarchy('handle')
tViewHandle = tHandle.register('handle', fields=[Field('view_id', tString)])
tObjHandle = tHandle.register('obj_handle', base=tViewHandle, fields=[Field('object', tObject)])

tRedirectHandle = tHandle.register('redirect', fields=[Field('redirect_to', tUrl)])


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
        return TOptional(tHandle)


class ContentsCommand(RequestCmd):

    def __init__( self, command_id, params_fields=None ):
        RequestCmd.__init__(self, command_id, params_fields)

    def get_result_type( self, iface ):
        return iface.get_contents_type()


class Interface(object):

    # client request types
    rt_request = 1
    rt_notification =2

    def __init__( self, iface_id, base=None, content_fields=None, diff_type=tNone, commands=None, required_module_id=None ):
        assert base is None or isinstance(base, Interface), repr(base)
        assert is_list_inst(content_fields or [], Field), repr(content_fields)
        assert diff_type is None or isinstance(diff_type, Type), repr(diff_type)
        assert is_list_inst(commands or [], (RequestCmd, NotificationCmd)), repr(commands)
        self.iface_id = iface_id
        self.content_fields = content_fields or []
        self.diff_type = diff_type
        self.commands = commands or []
        self.required_module_id = required_module_id
        if base:
            self.content_fields = base.content_fields + self.content_fields
            self.commands = base.commands + self.commands
            assert diff_type is tNone, repr(diff_type)  # Inherited from base
            self.diff_type = base.diff_type
        self.id2command = dict((cmd.command_id, cmd) for cmd in self.commands + self.get_basic_commands())
        self._register_types()

    def _register_types( self ):
        self._tContents = TRecord(self.get_contents_fields())
        self._command_params_t = dict((command_id, cmd.get_params_type(self)) for command_id, cmd in self.id2command.items())
        self._command_result_t = dict((command_id, cmd.get_result_type(self)) for command_id, cmd in self.id2command.items())
        self._tObject = tObject.register(self.iface_id, base=tThisProxyObjectWithContents, fields=[Field('contents', self._tContents)])
        tUpdate.register((self.iface_id,), self.diff_type)
        for command in self.id2command.values():
            cmd_id = command.command_id
            tClientNotificationRec.register((self.iface_id, cmd_id), self._command_params_t[cmd_id])
            tResponseRec.register((self.iface_id, cmd_id), self._command_result_t[cmd_id])

    def get_object_type( self ):
        return self._tObject

    def get_contents_type( self ):
        return self._tContents

    def get_module_ids( self ):
        if self.required_module_id:
            return [self.required_module_id]
        else:
            return []

    def get_basic_commands( self ):
        return [
            OpenCommand('get'),
            ContentsCommand('subscribe'),
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

    def _get_command( self, command_id ):
        cmd = self.id2command.get(command_id)
        if not cmd:
            raise TypeError('%s: Unsupported command id: %r' % (self.iface_id, command_id))
        return cmd

    def get_request_params_type( self, command_id ):
        return self._command_params_t[command_id]

    def make_params( self, command_id, *args, **kw ):
        return self.get_request_params_type(command_id)(*args, **kw)

    def get_command_result_type( self, command_id ):
        return self._command_result_t[command_id]

    def make_result( self, command_id, *args, **kw ):
        return self.get_command_result_type(command_id)(*args, **kw)

    def get_default_contents_fields( self ):
        return [Field('commands', TList(tCommand))]

    def get_contents_fields( self ):
        return self.get_default_contents_fields() + self.content_fields

    def Object( self, **kw ):
        return self._tObject(**kw)

    def Contents( self, **kw ):
        return self._tContents(**kw)

    def Update( self, path, diff ):
        return tUpdate(self.iface_id, path, diff)
        

class IfaceRegistry(object):

    def __init__( self ):
        self.registry = {}  # iface id -> Interface

    def register( self, iface ):
        assert isinstance(iface, Interface), repr(iface)
        self.registry[iface.iface_id] = iface

    def is_registered( self, iface_id ):
        return iface_id in self.registry

    def resolve( self, iface_id ):
        return self.registry[iface_id]


iface_registry = IfaceRegistry()

def register_iface( iface ):
    iface_registry.register(iface)

def resolve_iface( iface_id ):
    return iface_registry.resolve(iface_id)


# all interfaces support this one too:        
get_iface = Interface('base_get')

register_iface(get_iface)
