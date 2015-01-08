from iface import ObjectIface
import iface_registry


class TextObject(ObjectIface):

    def __init__( self, server, response ):
        ObjectIface.__init__(self, server, response)
        self.text = ''

    def text_changed( self, new_text ):
        self.text = new_text


iface_registry.register_iface('text', TextObject)
