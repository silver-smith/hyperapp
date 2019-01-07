import logging
from enum import Enum

from hyperapp.common.htypes import tString, Field
from hyperapp.client.module import ClientModule
from hyperapp.client.command import command
from hyperapp.client.object import Object
from . import htypes

log = logging.getLogger(__name__)


MODULE_NAME = 'text_object'


class TextObject(Object):

    impl_id = 'text'

    class Mode(Enum):
        VIEW = 'view'
        EDIT = 'edit'

    @classmethod
    def from_state(cls, state):
        return cls(state.text)

    @staticmethod
    def get_state_type():
        return htypes.text_object.text_object

    def __init__(self, text):
        self._text = text
        Object.__init__(self)

    def get_title(self):
        return 'Local text object'

    def get_state(self):
        return htypes.text_object.text_object(self.impl_id, self._text)

    def get_command_list(self, mode, kinds):
        assert mode in self.Mode, repr(mode)
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
        if mode is self.Mode.VIEW:
            return command.id != 'view'
        if mode is self.Mode.EDIT:
            return command.id != 'edit'
        assert False, repr(mode)  # Unknown mode

    def text_changed(self, new_text, emitter_view=None):
        self._text = new_text
        self._notify_object_changed(emitter_view)

    async def open_ref(self, ref_id):
        pass  # not implemented for local text

    def __del__(self):
        log.info('~text_object %r', self)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.objimpl_registry.register(TextObject.impl_id, TextObject.from_state)
