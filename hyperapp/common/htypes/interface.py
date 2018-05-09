import logging
from ..util import is_list_inst, cached_property
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
from .meta_type import TypeNamespace

log = logging.getLogger(__name__)


class IfaceCommand(TypeNamespace):

    # client request types
    rt_request = 'request'
    rt_notification = 'notification'

    def __init__(self, full_name, request_type, command_id, params_fields=None, result_fields=None):
        assert request_type in [self.rt_request, self.rt_notification], repr(request_type)
        assert isinstance(command_id, str), repr(command_id)
        assert is_list_inst(params_fields or [], Field), repr(params_fields)
        assert is_list_inst(result_fields or [], Field), repr(result_fields)
        super().__init__()
        self._full_name = full_name
        self.request_type = request_type
        self.command_id = command_id
        self.params_fields = params_fields or []
        self.result_fields = result_fields or []
        self['request'] = TRecord(self.params_fields, full_name=self._full_name + ['request'])
        if self.is_request:
            self['response'] = TRecord(self._make_response_fields(), full_name=self._full_name + ['response'])

    def __eq__(self, other):
        assert isinstance(other, IfaceCommand), repr(other)
        return (self._full_name == other._full_name and
                self.request_type == other.request_type and
                self.command_id == other.command_id and
                self.params_fields == other.params_fields and
                self.result_fields == other.result_fields)

    def __hash__(self):
        return hash((tuple(self._full_name), self.request_type, self.command_id, tuple(self.params_fields), tuple(self.result_fields)))

    @property
    def is_request(self):
        return self.request_type == self.rt_request

#    def _make_request_fields(self):
#        field_list = [
#            Field('command_id', tString),
#            ] + self.params_fields
#        if self.request_type == self.rt_request:
#            field_list = [Field('request_id', tString)] + field_list
#        return field_list

    def _make_response_fields(self):
        assert self.request_type == self.rt_request
        field_list = [
            Field('request_id', tString),
            Field('command_id', tString),
            ] + self.result_fields
        return field_list


class RequestCmd(IfaceCommand):

    def __init__(self, full_name, command_id, params_fields=None, result_fields=None):
        IfaceCommand.__init__(self, full_name, self.rt_request, command_id, params_fields, result_fields)


class NotificationCmd(IfaceCommand):

    def __init__(self, full_name, command_id, params_fields=None):
        IfaceCommand.__init__(self, full_name, self.rt_notification, command_id, params_fields)


class Interface(TypeNamespace):

    def __init__(self, full_name, base=None, commands=None):
        assert base is None or isinstance(base, Interface), repr(base)
        assert is_list_inst(commands or [], IfaceCommand), repr(commands)
        super().__init__()
        self._full_name = full_name
        self._base = base
        self._command_list = commands
        all_commands = self._command_list
        if base:
            all_commands += base._command_list
        for command in all_commands:
            self[command.command_id] = command

    def __eq__(self, other):
        return (isinstance(other, Interface) and
                other._base == self._base and
                other._command_list == self._command_list)

    def __hash__(self):
        return hash((
            self._base,
            tuple(self._command_list),
            ))

    @property
    def full_name(self):
        return self._full_name
