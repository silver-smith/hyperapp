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

    def __init__(self, request_type, command_id, params_fields=None, result_fields=None):
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

    def bind(self, iface, params_fields=None, result_fields=None, result_type=None):
        return BoundIfaceCommand(iface, self.request_type, self.command_id,
                                 params_fields or self.params_fields,
                                 result_fields or self.result_fields,
                                 result_type)


class RequestCmd(IfaceCommand):

    def __init__(self, command_id, params_fields=None, result_fields=None):
        IfaceCommand.__init__(self, self.rt_request, command_id, params_fields, result_fields)


class NotificationCmd(IfaceCommand):

    def __init__(self, command_id, params_fields=None):
        IfaceCommand.__init__(self, self.rt_notification, command_id, params_fields)


class ContentsCommand(RequestCmd):
    pass


class BoundIfaceCommand(object):

    def __init__(self, iface, request_type, command_id, params_fields, result_fields, result_type):
        assert not (result_fields and result_type)  # only one can be specified
        self.iface = iface
        self.request_type = request_type
        self.command_id = command_id
        self.params_fields = params_fields
        self.result_fields = result_fields
        self.params_type = TRecord(self.params_fields)
        self.result_type = result_type or TRecord(self.result_fields)


class Interface(object):

    def __init__(self, iface_id, base=None, contents_fields=None, diff_type=None, commands=None):
        assert base is None or isinstance(base, Interface), repr(base)
        assert is_list_inst(contents_fields or [], Field), repr(contents_fields)
        assert diff_type is None or isinstance(diff_type, Type), repr(diff_type)
        assert is_list_inst(commands or [], IfaceCommand), repr(commands)
        self.iface_id = iface_id
        self.base = base
        self._contents_fields = contents_fields or []
        self._diff_type = diff_type
        self._unbound_commands = commands or []
        if base:
            self._contents_fields = base._contents_fields + self._contents_fields
            assert diff_type is None, repr(diff_type)  # Inherited from base
            self._diff_type = base._diff_type

    def register_types(self, request_types, core_types):
        self._tContents = TRecord(self.get_contents_fields())  # used by the following commands params/result
        self._bound_commands = list(map(self._resolve_and_bind_command, self.get_basic_commands(core_types) + self._unbound_commands))
        self._id2command = dict((cmd.command_id, cmd) for cmd in self._bound_commands)
        self._tObject = core_types.object.register(
            self.iface_id, base=core_types.proxy_object_with_contents, fields=[Field('contents', self._tContents)])
        log.debug('### registered object %r in %r', self.iface_id, id(core_types.object))
        request_types.update.register((self.iface_id,), self._diff_type)
        for cmd_id, command in self._id2command.items():
            request_types.client_notification_rec.register((self.iface_id, cmd_id), self._id2command[cmd_id].params_type)
            request_types.result_response_rec.register((self.iface_id, cmd_id), self._id2command[cmd_id].result_type)
        self.tUpdate = request_types.update

    def __eq__(self, other):
        return (isinstance(other, Interface) and
                other.iface_id == self.iface_id and
                other.base == self.base and
                other._contents_fields == self._contents_fields and
                other._diff_type == self._diff_type and
                other._unbound_commands == self._unbound_commands)

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

    def _resolve_and_bind_command(self, command, params_fields=None, result_fields=None, result_type=None):
        if isinstance(command, ContentsCommand):
            result_type = self.get_contents_type()
        return command.bind(self, params_fields, result_fields, result_type)
        
    def _make_open_command(self, core_types, command_id, params_fields=None, result_fields=None):
        result_fields = [Field('handle', TOptional(core_types.handle))] + (result_fields or [])
        return RequestCmd(command_id, params_fields, result_fields)

    def get_commands(self):
        if self.base:
            return self.base._bound_commands + self._bound_commands
        else:
            return self._bound_commands

    def get_command(self, command_id):
        cmd = self._id2command.get(command_id)
        if not cmd:
            if self.base:
                return self.base.get_command(command_id)
            else:
                raise TypeError('%s: Unsupported command id: %r' % (self.iface_id, command_id))
        return cmd

    def make_params(self, command_id, *args, **kw):
        return self.get_command(command_id).params_type(*args, **kw)

    def make_result(self, command_id, *args, **kw):
        return self.get_command(command_id).result_type(*args, **kw)

    def get_default_contents_fields(self):
        return []

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
