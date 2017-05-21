import logging
from ..util import is_list_inst
from .htypes import (
    join_path,
    Type,
    tNone,
    tBinary,
    tString,
    TOptional,
    Field,
    TRecord,
    TList,
    tPath,
    tUrl,
    tIfaceId,
    tCommand,
    )
from .hierarchy import THierarchy

log = logging.getLogger(__name__)


class IfaceCommand(object):

    # client request types
    rt_request = 'request'
    rt_notification = 'notification'

    def __init__(self, request_type, command_id, params_fields, result_fields=None):
        assert request_type in [self.rt_request, self.rt_notification], repr(request_type)
        assert isinstance(command_id, str), repr(command_id)
        assert is_list_inst(params_fields or [], Field), repr(params_fields)
        assert is_list_inst(result_fields or [], Field), repr(result_fields)
        self.request_type = request_type
        self.command_id = command_id
        self.params_fields = params_fields or []
        self.result_fields = result_fields or []

    def __eq__(self, other):
        assert isinstance(other, IfaceCommand), repr(other)
        return (other.request_type == self.request_type and
                other.command_id == self.command_id and
                other.params_fields == self.params_fields and
                self.result_fields == self.result_fields)

    def get_params_type(self, iface):
        return TRecord(self.get_params_fields(iface))

    def get_result_type(self, iface):
        return TRecord(self.get_result_fields(iface))

    def get_params_fields(self, iface):
        return self.params_fields

    def get_result_fields(self, iface):
        return self.result_fields

    def get_result_field_type(self, field_name):
        for field in self.result_fields:
            if field.name == field_name:
                return field.type
        return None


class RequestCmd(IfaceCommand):

    def __init__(self, command_id, params_fields=None, result_fields=None):
        IfaceCommand.__init__(self, self.rt_request, command_id, params_fields, result_fields)


class NotificationCmd(IfaceCommand):

    def __init__(self, command_id, params_fields=None):
        IfaceCommand.__init__(self, self.rt_notification, command_id, params_fields)


class ContentsCommand(RequestCmd):

    def __init__(self, command_id, params_fields=None):
        RequestCmd.__init__(self, command_id, params_fields)

    def get_result_type(self, iface):
        return iface.get_contents_type()


class Interface(object):

    def __init__(self, iface_id, base=None, contents_fields=None, diff_type=None, commands=None):
        assert base is None or isinstance(base, Interface), repr(base)
        assert is_list_inst(contents_fields or [], Field), repr(contents_fields)
        assert diff_type is None or isinstance(diff_type, Type), repr(diff_type)
        assert is_list_inst(commands or [], IfaceCommand), repr(commands)
        self.iface_id = iface_id
        self._contents_fields = contents_fields or []
        self._diff_type = diff_type
        self._commands = commands or []
        if base:
            self._contents_fields = base._contents_fields + self._contents_fields
            self._commands = base._commands + self._commands
            assert diff_type is None, repr(diff_type)  # Inherited from base
            self._diff_type = base._diff_type

    def register_types(self, request_types, core_types):
        self._id2command = dict((cmd.command_id, cmd) for cmd in self._commands + self.get_basic_commands(core_types))
        self._tContents = TRecord(self.get_contents_fields())  # used by the following commands params/result
        self._tObject = core_types.object.register(
            self.iface_id, base=core_types.proxy_object_with_contents, fields=[Field('contents', self._tContents)])
        log.debug('### registered object %r in %r', self.iface_id, id(core_types.object))
        request_types.tUpdate.register((self.iface_id,), self._diff_type)
        self._command_params_t = dict((command_id, cmd.get_params_type(self)) for command_id, cmd in self._id2command.items())
        self._command_result_t = dict((command_id, cmd.get_result_type(self)) for command_id, cmd in self._id2command.items())
        for command in self._id2command.values():
            cmd_id = command.command_id
            request_types.tClientNotificationRec.register((self.iface_id, cmd_id), self._command_params_t[cmd_id])
            request_types.tResultResponseRec.register((self.iface_id, cmd_id), self._command_result_t[cmd_id])
        self.tUpdate = request_types.tUpdate

    def __eq__(self, other):
        return (isinstance(other, Interface) and
                other.iface_id == self.iface_id and
                other._contents_fields == self._contents_fields and
                other._diff_type == self._diff_type and
                other._commands == self._commands)

    def get_object_type(self):
        return self._tObject

    def get_contents_type(self):
        return self._tContents

    def get_basic_commands(self, core_types):
        return [
            self._make_open_command(core_types, 'get'),
            ContentsCommand('subscribe'),
            NotificationCmd('unsubscribe'),
            ]

    def _make_open_command(self, core_types, command_id, params_fields=None, result_fields=None):
        result_fields = [Field('handle', TOptional(core_types.handle))] + (result_fields or [])
        return RequestCmd(command_id, params_fields, result_fields)

    def get_request_type(self, command_id):
        assert command_id in self._id2command, repr(command_id)  # Unknown command id
        command = self._id2command[command_id]
        return command.request_type

    def get_commands(self):
        return self._commands

    def get_command(self, command_id):
        cmd = self._id2command.get(command_id)
        if not cmd:
            raise TypeError('%s: Unsupported command id: %r' % (self.iface_id, command_id))
        return cmd

    def get_request_params_type(self, command_id):
        return self._command_params_t[command_id]

    def make_params(self, command_id, *args, **kw):
        return self.get_request_params_type(command_id)(*args, **kw)

    def get_command_result_type(self, command_id):
        return self._command_result_t[command_id]

    def make_result(self, command_id, *args, **kw):
        return self.get_command_result_type(command_id)(*args, **kw)

    def get_default_contents_fields(self):
        return [Field('commands', TList(tCommand))]

    def get_contents_fields(self):
        return self.get_default_contents_fields() + self._contents_fields

    def Object(self, **kw):
        return self._tObject(**kw)

    def Contents(self, **kw):
        return self._tContents(**kw)

    def Update(self, path, diff):
        return self.tUpdate(self.iface_id, path, diff)
        

# all interfaces support this one too:
## get_iface = Interface('base_get')


class IfaceRegistry(object):

    def __init__(self):
        self.registry = {}  # iface id -> Interface
        ## self.register(get_iface)

    def register(self, iface):
        assert isinstance(iface, Interface), repr(iface)
        self.registry[iface.iface_id] = iface

    def is_registered(self, iface_id):
        return iface_id in self.registry

    def resolve(self, iface_id):
        return self.registry[iface_id]
