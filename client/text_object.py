from object import Object


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

    def __init__( self, text ):
        Object.__init__(self)
        self.text = text

    def get_title( self ):
        return 'Local text object'

    def get_commands( self, mode ):
        assert mode in [self.mode_view, self.mode_edit], repr(mode)
        return []

    def text_changed( self, emitter, new_text ):
        self.text = new_text
        self._notify_object_changed(emitter)

    def run_command( self, initiator_view, command_id ):
        # todo: handle 'open_ref' command for client-only object after multi-server support is added
        if command_id == 'edit':
            return self.run_command_edit()
        if command_id == 'view':
            return self.run_command_view()
        return Object.run_command(self, initiator_view, command_id)

    def run_command_edit( self ):
        return self.edit_handle_ctr(self)

    def run_command_view( self ):
        return self.view_handle_ctr(self)

    def open_ref( self, initiator_view, ref_id ):
        self.run_command(initiator_view, 'open_ref', ref_id=ref_id)

    def __del__( self ):
        print '~text_object', self
