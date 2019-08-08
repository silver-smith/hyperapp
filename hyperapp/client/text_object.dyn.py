import logging
from enum import Enum

from hyperapp.client.module import ClientModule
from hyperapp.client.command import command
from hyperapp.client.object import Object
from . import htypes

log = logging.getLogger(__name__)

MODULE_NAME = 'text_object'


class TextObject(Object):

    @classmethod
    def from_state(cls, state):
        return cls(state.text)

    def __init__(self, text):
        self._text = text
        Object.__init__(self)

    def get_title(self):
        return 'Local text object'

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
        self._notify_object_changed()

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
        services.object_registry.register_type(htypes.text_object.text_object, TextObject.from_state)
