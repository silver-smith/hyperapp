from pony.orm import db_session, Required
from util import str2id
from object import Object, Command
from module import ModuleCommand
from ponyorm_module import PonyOrmModule
from iface import TextObjectIface


MODULE_NAME = 'article'


class Article(Object):

    iface = TextObjectIface()
    view_id = 'text'

    def __init__( self, path ):
        Object.__init__(self, path)

    def get_commands( self ):
        return [Command('save', 'Save', 'Save article', 'Ctrl+S')]

    def run_command( self, command_id, request ):
        if command_id == 'save':
            return self.run_command_save(request)
        else:
            return Object.run_command(self, command_id)

    def run_command_save( self, request ):
        text = request['text']
        new_path = self.do_save(text)
        return dict(new_path=new_path)

    def do_save( self, text ):
        article_id = str2id(self.path.split('/')[-1])
        with db_session:
            if article_id is not None:
                article_rec = module.Article[article_id]
            else:
                article_rec = None
            article_rec = self.save_article(article_rec, text)
        print 'Article is saved, article_id =', article_rec.id
        return '/article/%d' % article_rec.id

    def save_article( self, article_rec, text ):
        if article_rec is not None:
            article_rec.text = text
        else:
            article_rec = module.Article(text=text)
        return article_rec


class ArticleModule(PonyOrmModule):

    def __init__( self ):
        PonyOrmModule.__init__(self, MODULE_NAME)
        self.article_fields = dict(text=Required(unicode))

    def init_phase2( self ):
        self.Article = self.make_entity('Article', **self.article_fields)

    def get_commands( self ):
        return [ModuleCommand('create', 'Create article', 'Create new article', 'Alt+A', self.name)]

    def run_command( self, command_id ):
        if command_id == 'create':
            return Article('/article/new')
        assert False, repr(command_id)  # Unsupported command

    def add_article_fields( self, **fields ):
        self.article_fields.update(fields)


module = ArticleModule()
