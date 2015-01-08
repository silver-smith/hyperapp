from iface import ObjectIface
import iface_registry


class TextObject(ObjectIface):

    def __init__( self, server, response ):
        ObjectIface.__init__(self, server, response)
        self.text = ''
        ident = self.path.rsplit('/')[-1]
        if ident == 'new':
            self.article_id = None
        else:
            self.article_id = int(ident)

    def text_changed( self, new_text ):
        self.text = new_text

    def run_command( self, command_id ):
        if command_id == 'save':
            return self.run_command_save()
        return ObjectIface.run_command(self, command_id)

    def run_command_save( self ):
        request = dict(self.make_command_request(command_id='save'),
                       article_id=self.article_id,
                       text=self.text)
        response = self.server.execute_request(request)
        if self.article_id is None:
            self.article_id = response['article_id']
            head, tail = self.path.rsplit('/', 1)
            self.path = head + '/' + str(self.article_id)


iface_registry.register_iface('text', TextObject)
