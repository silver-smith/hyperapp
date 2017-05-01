import logging
import asyncio
from ..common.htypes import tString, Field
from ..common.interface import core as core_types
from ..common.interface import text_object_types
from .module import Module
from .command import open_command
from .object import Object

log = logging.getLogger(__name__)


def register_object_implementations(registry, serevices):
    registry.register(TextObject.objimpl_id, TextObject.from_state)


class TextObject(Object):

    objimpl_id = 'text'

    mode_view = object()
    mode_edit = object()

    @classmethod
    def from_state(cls, state, server=None):
        return cls(state.text)

    @staticmethod
    def get_state_type():
        return this_module.state_type

    def __init__(self, text):
        Object.__init__(self)
        self.text = text

    def get_title(self):
        return 'Local text object'

    def get_state(self):
        return this_module.state_type(self.objimpl_id, self.text)

    def get_commands(self, mode):
        assert mode in [self.mode_view, self.mode_edit], repr(mode)
        return self.filter_mode_commands(Object.get_commands(self), mode)

    def filter_mode_commands(self, commands, mode):
        return [command for command in commands
                if self.command_must_be_visible_for_mode(command, mode)]

    def command_must_be_visible_for_mode(self, command, mode):
        if mode is self.mode_view:
            return command.id != 'view'
        if mode is self.mode_edit:
            return command.id != 'edit'
        assert False, repr(mode)  # Unknown mode

    def text_changed(self, new_text, emitter_view=None):
        self.text = new_text
        self._notify_object_changed(emitter_view)

    @open_command('edit')
    def command_edit(self):
        return core_types.obj_handle('text_edit', self.get_state())

    @open_command('view')
    def command_view(self):
        return core_types.obj_handle('text_view', self.get_state())

    @asyncio.coroutine
    def open_ref(self, ref_id):
        pass  # not implemented for local text

    def __del__(self):
        log.info('~text_object %r', self)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self.state_type = text_object_types.text_object
