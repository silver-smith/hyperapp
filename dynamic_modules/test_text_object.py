# for type modules load testing

import logging
from ..common.htypes import tString, Field
from ..common.interface import core as core_types
from ..common.interface import text_object as text_object_types
from .command import command
from .object import Object
from . import text_object as original_text_object

log = logging.getLogger(__name__)


state_type = text_object_types.text_object


def register_object_implementations(registry, serevices):
    registry.register(TextObject.impl_id, TextObject.from_state)


class TextObject(Object):

    impl_id = 'test_text'

    Mode = original_text_object.TextObject.Mode

    @classmethod
    def from_state(cls, state, server=None):
        return cls(state.text)

    def __init__(self, text):
        Object.__init__(self)
        self.text = text

    def get_title(self):
        return 'Local text object'

    def get_state(self):
        return state_type(self.impl_id, self.text)

    def get_commands(self, mode):
        assert mode in self.Mode, repr(mode)
        return Object.get_commands(self)

    def text_changed(self, new_text, emitter_view=None):
        self.text = new_text
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
