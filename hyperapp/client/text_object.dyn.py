import logging
from ..common.htypes import tString, Field
from ..common.interface import core as core_types
from ..common.interface import text_object_types
from .module import Module
from .command import command
from .object import Object

log = logging.getLogger(__name__)


def register_object_implementations(registry, serevices):
    registry.register(TextObject.impl_id, TextObject.from_state)


class TextObject(Object):

    impl_id = 'text'

    mode_view = object()
    mode_edit = object()

    @classmethod
    def from_state(cls, state, server=None):
        return cls(state.text)

    @staticmethod
    def get_state_type():
        return text_object_types.text_object

    def __init__(self, text):
        self._text = text
        Object.__init__(self)

    def get_title(self):
        return 'Local text object'

    def get_state(self):
        return text_object_types.text_object(self.impl_id, self._text)

    def get_command_list(self, mode, kinds):
        assert mode in [self.mode_view, self.mode_edit], repr(mode)
        return self.filter_mode_commands(Object.get_command_list(self, kinds), mode)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
        self._notify_object_changed()

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
        self._text = new_text
        self._notify_object_changed(emitter_view)

    @command('edit')
    def command_edit(self):
        return core_types.obj_handle('text_edit', self.get_state())

    @command('view')
    def command_view(self):
        return core_types.obj_handle('text_view', self.get_state())

    async def open_ref(self, ref_id):
        pass  # not implemented for local text

    def __del__(self):
        log.info('~text_object %r', self)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
