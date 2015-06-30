from datetime import datetime
from pony.orm import db_session, commit, desc, Required, Set
from ponyorm_module import PonyOrmModule
from util import utcnow, str2id
from common.interface import Command
from common.interface.blog import blog_entry_iface, blog_iface
from common.request import ListDiff, Element, Column, DateTimeColumnType
from object import ListObject, subscription
from module import ModuleCommand
import article


MODULE_NAME = 'blog'


class BlogEntry(article.Article):

    iface = blog_entry_iface
    proxy_id = 'text'

    @classmethod
    def make_path( cls, article_id ):
        return module.make_path(object='entry', article_id=article_id)

    @classmethod
    def make( cls, article_id, mode=article.Article.mode_view ):
        return cls(cls.make_path(article_id), article_id, mode)

    @classmethod
    def from_path( cls, path ):
        article_id = path['article_id']
        return cls(path, article_id)

    def get_commands( self ):
        return [
            Command('parent', 'Parent', 'Open parent article', 'Ctrl+Backspace'),
            ] + article.Article.get_commands(self)

    def process_request( self, request ):
        if request.command_id == 'parent':
            return self.run_command_parent(request)
        return article.Article.process_request(self, request)
    
    def run_command_parent( self, request ):
        return request.make_response_object(Blog.make())

    @db_session
    def do_save( self, request, text ):
        if self.article_id is not None:
            entry_rec = module.BlogEntry[self.article_id]
            entry_rec.text = text
        else:
            entry_rec = module.BlogEntry(
                text=text,
                created_at=utcnow())
        commit()
        print 'Blog entry is saved, blog entry id =', entry_rec.id
        new_path = dict(self.path, article_id=entry_rec.id)
        subscription.distribute_update(new_path, article.TextDiff(text))
        diff = ListDiff.add_one(entry_rec.id, Blog.rec2element(entry_rec))
        subscription.distribute_update(Blog.make_path(), diff)
        return request.make_response_result(new_path=new_path)


class Blog(ListObject):

    iface = blog_iface
    proxy_id = 'list'
    view_id = 'list'

    columns = [
        Column('key', 'Article id'),
        Column('created_at', 'Creation date', type=DateTimeColumnType()),
        ]

    @classmethod
    def make( cls ):
        return cls(cls.make_path())

    @classmethod
    def make_path( cls ):
        return module.make_path(object='blog')

    def __init__( self, path ):
        ListObject.__init__(self, path)

    def get_commands( self ):
        return [Command('add', 'Add entry', 'Create new blog entry', 'Ins')]

    def process_request( self, request ):
        if request.command_id == 'add':
            return self.run_command_add(request)
        if request.command_id == 'open':
            article_id = request.params.element_key
            return request.make_response_object(BlogEntry.make(article_id=article_id))
        if request.command_id == 'delete':
            return self.run_element_command_delete(request)
        return ListObject.process_request(self, request)

    def run_command_add( self, request ):
        return request.make_response_object(BlogEntry.make(article_id=None, mode=BlogEntry.mode_edit))

    @db_session
    def get_all_elements( self ):
        return map(self.rec2element, module.BlogEntry.select().order_by(desc(module.BlogEntry.created_at)))

    @staticmethod
    def rec2element( rec ):
        commands = [Command('open', 'Open', 'Open blog entry'),
                    Command('delete', 'Delete', 'Delete blog entry', 'Del'),
                    ]
        return Element(rec.id, [rec.id, rec.created_at], commands)

    @db_session
    def run_element_command_delete( self, request ):
        article_id = request.params.element_key
        module.BlogEntry[article_id].delete()
        diff = ListDiff.delete(article_id)
        return request.make_response_update(self.iface, self.path, diff)


class BlogModule(PonyOrmModule):

    def __init__( self ):
        PonyOrmModule.__init__(self, MODULE_NAME)
        self.article_module = article.module

    def init_phase2( self ):
        self.Article = self.article_module.Article
        self.BlogEntry = self.make_inherited_entity('BlogEntry', self.Article,
                                                    created_at=Required(datetime))
        BlogEntry.register_class(self.BlogEntry)

    def resolve( self, path ):
        objname = path.get('object')
        if objname == 'blog':
            return Blog(path)
        if objname == 'entry':
            return BlogEntry.from_path(path)
        assert objname is None, repr(objname)  # Unknown object name
        return PonyOrmModule.resolve(self, path)

    def get_commands( self ):
        return [
            ModuleCommand('create', 'Create entry', 'Create new blog entry', None, self.name),
            ModuleCommand('open_blog', 'Blog', 'Open blog', 'Alt+B', self.name),
            ]

    def run_command( self, request, command_id ):
        if command_id == 'create':
            return request.make_response_object(BlogEntry.make(article_id=None))
        if command_id == 'open_blog':
            return request.make_response_object(Blog.make())
        return PonyOrmModule.run_command(self, request, command_id)


module = BlogModule()
