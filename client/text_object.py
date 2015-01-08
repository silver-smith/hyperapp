from iface import ObjectIface
import iface_registry


class TextObject(ObjectIface):

    def __init__( self, server, response ):
        ObjectIface.__init__(self, server, response)
        self.text = ''

    def text_changed( self, new_text ):
        self.text = new_text

    def run_command( self, command_id ):
        if command_id == 'save':
            return self.run_command_save()
        return ObjectIface.run_command(self, command_id)

    def run_command_save( self ):
        request = dict(self.make_command_request(command_id='save'),
                       text=self.text)
        return self.server.get_view(request)


iface_registry.register_iface('text', TextObject)
