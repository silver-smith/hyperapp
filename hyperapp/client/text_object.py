from ..common.interface import tString, tObject, Field, tBaseObject, tHandle
from .object import Object
from .objimpl_registry import objimpl_registry


dataType = tObject.register('text', base=tBaseObject, fields=[Field('text', tString)])


class TextObject(Object):

    mode_view = object()
    mode_edit = object()

    view_handle_ctr = None
    edit_handle_ctr = None

    @classmethod
    def set_view_handle_ctr( cls, ctr ):
        cls.view_handle_ctr = ctr

    @classmethod
    def set_edit_handle_ctr( cls, ctr ):
        cls.edit_handle_ctr = ctr

    @classmethod
    def factory( cls, objinfo, server=None ):
        return cls(objinfo.text)

    def __init__( self, text ):
        Object.__init__(self)
        self.text = text

    def get_title( self ):
        return 'Local text object'

    def to_data( self ):
        return dataType.instantiate('text', self.text)

    def get_commands( self, mode ):
        assert mode in [self.mode_view, self.mode_edit], repr(mode)
        return []

    def text_changed( self, new_text, emitter_view=None ):
        self.text = new_text
        self._notify_object_changed(emitter_view)

    def run_command( self, command_id, initiator_view=None, **kw ):
        # todo: handle 'open_ref' command by client-only object after multi-server support is added
        if command_id == 'edit':
            return self.run_command_edit()
        if command_id == 'view':
            return self.run_command_view()
        return Object.run_command(self, command_id, initiator_view, **kw)

    def run_command_edit( self ):
        return self.edit_handle_ctr(self)

    def run_command_view( self ):
        return self.view_handle_ctr(self)

    def open_ref( self, initiator_view, ref_id ):
        self.run_command('open_ref', initiator_view, ref_id=ref_id)

    def __del__( self ):
        print '~text_object', self


objimpl_registry.register('text', TextObject.factory)
