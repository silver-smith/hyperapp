from pony.orm import db_session, Required, Optional, Set
from util import str2id
from object import Object, ListObject, Command, Element, Column
from module import ModuleCommand
from ponyorm_module import PonyOrmModule
from iface import Iface, TextObjectIface, ListIface


MODULE_NAME = 'article'


class Article(Object):

    iface = TextObjectIface()
    view_id = 'text'

    def __init__( self, path ):
        Object.__init__(self, path)

    @db_session
    def get_json( self ):
        article_id = self.get_article_id()
        if article_id is not None:
            rec = module.Article[article_id]
            text = rec.text
        else:
            text = None
        return dict(
            Object.get_json(self),
            text=text)

    def get_commands( self ):
        return [
            Command('save', 'Save', 'Save article', 'Ctrl+S'),
            Command('refs', 'Refs', 'Open article references', 'Ctrl+R'),
            ]

    def run_command( self, command_id, request ):
        if command_id == 'save':
            return self.run_command_save(request)
        elif command_id == 'refs':
            return self.run_command_refs(request)
        else:
            return Object.run_command(self, command_id, request)

    def run_command_save( self, request ):
        text = request['text']
        new_path = self.do_save(text)
        return dict(new_path=new_path)

    def run_command_refs( self, request ):
        return ArticleRefList('%s/refs' % self.path)

    def get_article_id( self ):
        return str2id(self.path.split('/')[-1])

    def do_save( self, text ):
        article_id = self.get_article_id()
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


class ArticleRefList(ListObject):

    iface = ListIface()
    view_id = 'list'

    columns = [
        Column('key', 'Ref id'),
        Column('path', 'Path'),
        ]

    def get_commands( self ):
        return [Command('add', 'Add ref', 'Create new reference', 'Ins')]

    def run_command( self, command_id, request ):
        if command_id == 'add':
            return ArticleRef(self.path + '/new')
        assert False, repr(command_id)  # Unsupported command

    def get_article_id( self ):
        return str2id(self.path.split('/')[-2])

    @db_session
    def get_all_elements( self ):
        return map(self.rec2element, module.Article[self.get_article_id()].refs)

    def rec2element( self, rec ):
        return Element(rec.id, [rec.id, rec.path])



class ArticleRefIface(Iface):

    id = 'article_ref'


class ArticleRef(Object):

    iface = ArticleRefIface()
    view_id = 'article_ref'


class ArticleModule(PonyOrmModule):

    def __init__( self ):
        PonyOrmModule.__init__(self, MODULE_NAME)
        self.article_fields = dict(text=Required(unicode),
                                   refs=Set('ArticleRef'))

    def init_phase2( self ):
        self.Article = self.make_entity('Article', **self.article_fields)
        self.ArticleRef = self.make_entity('ArticleRef',
                                           article=Required(self.Article),
                                           path=Optional(str),
                                           )

    def get_commands( self ):
        return [ModuleCommand('create', 'Create article', 'Create new article', 'Alt+A', self.name)]

    def run_command( self, command_id ):
        if command_id == 'create':
            return Article('/article/new')
        assert False, repr(command_id)  # Unsupported command

    def add_article_fields( self, **fields ):
        self.article_fields.update(fields)


module = ArticleModule()
