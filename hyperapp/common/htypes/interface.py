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

    def __hash__(self):
        return hash((self.request_type, self.command_id, tuple(self.params_fields), tuple(self.result_fields)))

    @property
    def is_request(self):
        return self.request_type == self.rt_request

    @property
    def request_t(self):
        field_list = [
            Field('command_id', tString),
            ] + self.params_fields
        if self.request_type == self.rt_request:
            field_list = [Field('request_id', tString)] + field_list
        return field_list

    @property
    def response_t(self):
        assert self.request_type == self.rt_request
        return [
            Field('request_id', tString),
            Field('command_id', tString),
            ] + self.result_fields


class RequestCmd(IfaceCommand):

    def __init__(self, command_id, params_fields=None, result_fields=None):
        IfaceCommand.__init__(self, self.rt_request, command_id, params_fields, result_fields)


class NotificationCmd(IfaceCommand):

    def __init__(self, command_id, params_fields=None):
        IfaceCommand.__init__(self, self.rt_notification, command_id, params_fields)


class Interface(object):

    def __init__(self, iface_id, base=None, contents_fields=None, diff_type=None, commands=None):
        assert base is None or isinstance(base, Interface), repr(base)
        assert is_list_inst(commands or [], IfaceCommand), repr(commands)
        self._base = base
        self._command_list = commands
        self._id2command = {command.command_id: command for command in self._command_list}

    def __eq__(self, other):
        return (isinstance(other, Interface) and
                other._base == self._base and
                other._command_list == self._command_list)

    def __hash__(self):
        return hash((
            self._base,
            tuple(self._command_list),
            ))

    def get_command(self, command_id):
        command = self._id2command.get(command_id)
        if command:
            return command
        if self._base:
            return self._base.get_command(command_id)
        return None


# todo: obsolete, remove
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
