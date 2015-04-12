# text object representing server text object

from text_object import TextObject
from proxy_object import ProxyObject
import iface_registry


class ProxyTextObject(ProxyObject, TextObject):

    @classmethod
    def from_resp( cls, server, resp ):
        path, commands = ProxyObject.parse_resp(resp)
        text = resp['text']
        return cls(server, path, commands, text)

    def __init__( self, server, path, commands, text ):
        TextObject.__init__(self, text)
        ProxyObject.__init__(self, server, path, commands)

    def get_commands( self, mode ):
        assert mode in [self.mode_view, self.mode_edit], repr(mode)
        commands = []
        for cmd in ProxyObject.get_commands(self):
            if mode is self.mode_view and cmd.id in ['view', 'save']: continue
            if mode is self.mode_edit and cmd.id in ['edit']: continue
            commands.append(cmd)
        return commands

    def run_command( self, command_id ):
        if command_id == 'edit' or command_id == 'view':
            return TextObject.run_command(self, command_id)
        return ProxyObject.run_command(self, command_id)

    def prepare_command_request( self, command_id, **kw ):
        if command_id == 'save':
            return ProxyObject.prepare_command_request(self, command_id, text=self.text, **kw)
        return ProxyObject.prepare_command_request(self, command_id, **kw)

    def process_response_result( self, request_method, result ):
        if request_method == 'save':
            self.path = result.new_path


iface_registry.register_iface('text', ProxyTextObject.from_resp)
