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
            self['response'] = TRecord(self.result_fields, full_name=self._full_name + ['response'])

    @property
    def full_name(self):
        return self._full_name

    @property
    def is_request(self):
        return self.request_type == self.rt_request


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

    @property
    def full_name(self):
        return self._full_name

    @property
    def base(self):
        return self._base
