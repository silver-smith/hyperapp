from proxy_object import ProxyObject
import iface_registry


class TextObject(ProxyObject):

    @classmethod
    def from_resp( cls, server, resp ):
        path, commands = ProxyObject.parse_resp(resp)
        text = resp['text']
        return cls(server, path, commands, text)

    def __init__( self, server, path, commands, text ):
        ProxyObject.__init__(self, server, path, commands)
        self.text = text

    def text_changed( self, new_text ):
        self.text = new_text

    def run_command( self, command_id ):
        if command_id == 'save':
            return self.run_command_save()
        return ProxyObject.run_command(self, command_id)

    def run_command_save( self ):
        request = dict(self.make_command_request(command_id='save'),
                       text=self.text)
        response = self.server.execute_request(request)
        self.path = response.result.new_path

    def open_ref( self, ref_id ):
        request = dict(self.make_command_request(command_id='open_ref'),
                       ref_id=ref_id)
        return self.server.request_an_object(request)
        


iface_registry.register_iface('text', TextObject.from_resp)
