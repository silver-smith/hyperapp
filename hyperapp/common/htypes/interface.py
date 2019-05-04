from collections import OrderedDict
import logging

from ..util import is_list_inst, is_ordered_dict_inst, cached_property
from .htypes import (
    join_path,
    list_all_match,
    odict_all_match,
    Type,
    tNone,
    tBinary,
    tString,
    TOptional,
    TRecord,
    TList,
    tPath,
    tUrl,
    tIfaceId,
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
        assert params_fields is None or is_ordered_dict_inst(params_fields, str, Type), repr(params_fields)
        assert result_fields is None or is_ordered_dict_inst(result_fields, str, Type), repr(result_fields)
        super().__init__()
        self._full_name = full_name
        self.request_type = request_type
        self.command_id = command_id
        self.params_fields = params_fields or OrderedDict()
        self.result_fields = result_fields or OrderedDict()
        self['request'] = TRecord('_'.join(self._full_name + ['request']), self.params_fields)
        if self.is_request:
            self['response'] = TRecord('_'.join(self._full_name + ['response']), self.result_fields)

    def match(self, other):
        assert isinstance(other, IfaceCommand), repr(other)
        return (self._full_name == other._full_name and
                self.request_type == other.request_type and
                self.command_id == other.command_id and
                odict_all_match(self.params_fields, other.params_fields) and
                odict_all_match(self.result_fields, other.result_fields))

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

    def match(self, other):
        return (isinstance(other, Interface)
                and (self._base is other._base is None or other._base.match(self._base))
                and list_all_match(other._command_list, self._command_list))

    @property
    def full_name(self):
        return self._full_name

    @property
    def base(self):
        return self._base
