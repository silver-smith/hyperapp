# for type modules load testing

import logging
import asyncio
from ..common.htypes import tString, tObject, Field, tBaseObject, tObjHandle
from ..common.interface import text_object_types
from .command import open_command
from .object import Object
from . import text_object as original_text_object

log = logging.getLogger(__name__)


state_type = text_object_types.text_object


def register_object_implementations( registry, serevices ):
    registry.register(TextObject.objimpl_id, TextObject.from_state)


class TextObject(Object):

    objimpl_id = 'test_text'

    mode_view = original_text_object.TextObject.mode_view
    mode_edit = original_text_object.TextObject.mode_edit

    @classmethod
    def from_state( cls, state, server=None ):
        return cls(state.text)

    def __init__( self, text ):
        Object.__init__(self)
        self.text = text

    def get_title( self ):
        return 'Local text object'

    def get_state( self ):
        return state_type(self.objimpl_id, self.text)

    def get_commands( self, mode ):
        assert mode in [self.mode_view, self.mode_edit], repr(mode)
        return Object.get_commands(self)

    def text_changed( self, new_text, emitter_view=None ):
        self.text = new_text
        self._notify_object_changed(emitter_view)

    @open_command('edit')
    def command_edit( self ):
        return tObjHandle('text_edit', self.get_state())

    @open_command('view')
    def command_view( self ):
        return tObjHandle('text_view', self.get_state())

    @asyncio.coroutine
    def open_ref( self, ref_id ):
        pass  # not implemented for local text

    def __del__( self ):
        log.info('~text_object %r', self)
