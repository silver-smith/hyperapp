from pony.orm import db_session, Required
from object import Object, Command
from module import ModuleCommand
from ponyorm_module import PonyOrmModule
from iface import TextObjectIface


MODULE_NAME = 'article'


class Article(Object):

    iface = TextObjectIface()
    view_id = 'text'

    def __init__( self, article_id=None ):
        Object.__init__(self, '/article/new')
        self.id = article_id

    def get_commands( self ):
        return [Command('save', 'Save', 'Save article', 'Ctrl+S')]

    def run_command( self, command_id ):
        if command_id == 'save':
            return self.run_command_save()
        else:
            return Object.run_command(self, command_id)

    def run_command_save( self ):
        pass


class ArticleModule(PonyOrmModule):

    def __init__( self ):
        PonyOrmModule.__init__(self, MODULE_NAME)
        self.Article = self.make_entity('Article',
                                        text=Required(unicode))

    def get_commands( self ):
        return [ModuleCommand('create', 'Create article', 'Create new article', 'Alt+A', self.name)]

    def run_command( self, command_id ):
        if command_id == 'create':
            return Article()
        assert False, repr(command_id)  # Unsupported command


module = ArticleModule()
