import logging
import asyncio
from ..common.htypes import tString, tObject, Field, tBaseObject, tHandle, tObjHandle
from .object import Object

log = logging.getLogger(__name__)


def register_object_implementations( registry, serevices ):
    registry.register(TextObject.objimpl_id, TextObject.from_state)


state_type = tObject.register('text', base=tBaseObject, fields=[Field('text', tString)])


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
        return state_type('text', self.text)

    def get_commands( self, mode ):
        assert mode in [self.mode_view, self.mode_edit], repr(mode)
        return Object.get_commands(self)

    def text_changed( self, new_text, emitter_view=None ):
        self.text = new_text
        self._notify_object_changed(emitter_view)

    @asyncio.coroutine
    def run_command( self, command_id, **kw ):
        # todo: handle 'open_ref' command by client-only object after multi-server support is added
        if command_id == 'edit':
            return self.run_command_edit()
        if command_id == 'view':
            return self.run_command_view()
        return (yield from Object.run_command(self, command_id, **kw))

    def run_command_edit( self ):
        return tObjHandle('text_edit', self.get_state())

    def run_command_view( self ):
        return tObjHandle('text_view', self.get_state())

    @asyncio.coroutine
    def open_ref( self, ref_id ):
        return (yield from self.run_command('open_ref', ref_id=ref_id))

    def __del__( self ):
        log.info('~text_object %r', self)
