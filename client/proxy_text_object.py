# text object representing server text object

from text_object import TextObject
from proxy_object import ProxyObject
import proxy_registry


class ProxyTextObject(ProxyObject, TextObject):

    def __init__( self, server, path ):
        TextObject.__init__(self, text='')
        ProxyObject.__init__(self, server, path)

    def set_contents( self, contents ):
        ProxyObject.set_contents(self, contents)
        self.text = contents['text']

    def get_commands( self, mode ):
        assert mode in [self.mode_view, self.mode_edit], repr(mode)
        commands = []
        for cmd in ProxyObject.get_commands(self):
            if mode is self.mode_view and cmd.id in ['view', 'save']: continue
            if mode is self.mode_edit and cmd.id in ['edit']: continue
            commands.append(cmd)
        return commands

    def run_command( self, initiator_view, command_id, **kw ):
        if command_id == 'edit' or command_id == 'view':
            return TextObject.run_command(self, initiator_view, command_id, **kw)
        return ProxyObject.run_command(self, initiator_view, command_id, **kw)

    def prepare_command_request( self, command_id, **kw ):
        if command_id == 'save':
            return ProxyObject.prepare_command_request(self, command_id, text=self.text, **kw)
        return ProxyObject.prepare_command_request(self, command_id, **kw)

    def process_command_response_result( self, command_id, result ):
        if command_id == 'save':
            self.path = result.new_path
            self._notify_object_changed()


proxy_registry.register_iface('text', ProxyTextObject.from_response)
