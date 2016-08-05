import logging
import asyncio
from ..common.htypes import tString, tObject, Field, tBaseObject, tHandle, tObjHandle
from ..common.interface.text_object import tTextObject
from .command import command
from .object import Object

log = logging.getLogger(__name__)


def register_object_implementations( registry, serevices ):
    registry.register(TextObject.objimpl_id, TextObject.from_state)


class TextObject(Object):

    objimpl_id = 'text'

    mode_view = object()
    mode_edit = object()

    @classmethod
    def from_state( cls, state, server=None ):
        return cls(state.text)

    def __init__( self, text ):
        Object.__init__(self)
        self.text = text

    def get_title( self ):
        return 'Local text object'

    def get_state( self ):
        return tTextObject('text', self.text)

    def get_commands( self, mode ):
        assert mode in [self.mode_view, self.mode_edit], repr(mode)
        return Object.get_commands(self)

    def text_changed( self, new_text, emitter_view=None ):
        self.text = new_text
        self._notify_object_changed(emitter_view)

    @command('edit')
    def command_edit( self ):
        return tObjHandle('text_edit', self.get_state())

    @command('view')
    def run_command_view( self ):
        return tObjHandle('text_view', self.get_state())

    @asyncio.coroutine
    def open_ref( self, ref_id ):
        pass  # not implemented for local text

    def __del__( self ):
        log.info('~text_object %r', self)
