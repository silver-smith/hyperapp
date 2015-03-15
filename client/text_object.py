from proxy_object import ProxyObject
import iface_registry
import view_registry


class TextObject(ProxyObject):

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
    def from_resp( cls, server, resp ):
        path, commands = ProxyObject.parse_resp(resp)
        text = resp['text']
        return cls(server, path, commands, text)

    def __init__( self, server, path, commands, text ):
        ProxyObject.__init__(self, server, path, commands)
        self.text = text

    def get_commands( self, mode ):
        assert mode in [self.mode_view, self.mode_edit], repr(mode)
        commands = []
        for cmd in ProxyObject.get_commands(self):
            if mode is self.mode_view and cmd.id in ['view', 'save']: continue
            if mode is self.mode_edit and cmd.id in ['edit']: continue
            commands.append(cmd)
        return commands

    def text_changed( self, emitter, new_text ):
        self.text = new_text
        self._notify_object_changed(emitter)

    def run_command( self, command_id ):
        if command_id == 'edit':
            return self.run_command_edit()
        if command_id == 'view':
            return self.run_command_view()
        if command_id == 'save':
            return self.run_command_save()
        return ProxyObject.run_command(self, command_id)

    def run_command_edit( self ):
        return self.edit_handle_ctr(self)

    def run_command_view( self ):
        return self.view_handle_ctr(self)

    def run_command_save( self ):
        request = dict(self.make_command_request(command_id='save'),
                       text=self.text)
        response = self.server.execute_request(request)
        self.path = response.result.new_path

    def open_ref( self, ref_id ):
        request = dict(self.make_command_request(command_id='open_ref'),
                       ref_id=ref_id)
        return self.server.request_an_object(request)

    def __del__( self ):
        print '~text_object', self
        


iface_registry.register_iface('text', TextObject.from_resp)
