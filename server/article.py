from object import Object, Command
from module import Module, ModuleCommand
from iface import ObjectIface


MODULE_NAME = 'article'


class Article(Object):

    iface = ObjectIface()
    view_id = 'text'

    def __init__( self, article_id=None ):
        Object.__init__(self, '/article/new')
        self.id = article_id


class ArticleModule(Module):

    def __init__( self ):
        Module.__init__(self, MODULE_NAME)

    def get_commands( self ):
        return [ModuleCommand('create', 'Create article', 'Create new article', 'Alt+A', self.name)]

    def run_command( self, command_id ):
        if command_id == 'create':
            return Article()
        assert False, repr(command_id)  # Unsupported command


module = ArticleModule()
