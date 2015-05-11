from datetime import datetime
from pony.orm import db_session, commit, desc, Required, Set
from ponyorm_module import PonyOrmModule
from util import utcnow, str2id
from object import ListDiff, ListObject, Command, Element, Column
from module import ModuleCommand
from iface import ListIface
import article


MODULE_NAME = 'blog'


class BlogEntry(article.Article):

    @classmethod
    def make( cls, article_id, mode=article.Article.mode_view ):
        return cls(module.make_path(object='entry', article_id=article_id), article_id, mode)

    @classmethod
    def from_path( cls, path ):
        article_id = path['article_id']
        return cls(path, article_id)

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
        response = request.make_response()
        response.result.new_path = new_path
        diff = ListDiff.add_one(entry_rec.id, Blog.rec2element(entry_rec))
        response.add_update(module.get_blog_path(), diff)
        return response


class Blog(ListObject):

    iface = ListIface()
    view_id = 'list'

    columns = [
        Column('key', 'Article id'),
        Column('created_at', 'Creation date', type='datetime'),
        ]

    def __init__( self, path ):
        ListObject.__init__(self, path)

    def get_commands( self ):
        return [Command('add', 'Add entry', 'Create new blog entry', 'Ins')]

    def run_command( self, request, command_id ):
        if command_id == 'add':
            return self.run_command_add(request)
        return ListObject.run_command(self, request, command_id)

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

    def run_element_command( self, request, command_id, element_key ):
        if command_id == 'open':
            article_id = element_key
            return request.make_response_object(BlogEntry.make(article_id=element_key))
        if command_id == 'delete':
            return self.run_element_command_delete(request, element_key)
        return ListObject.run_element_command(self, request, command_id, element_key)

    @db_session
    def run_element_command_delete( self, request, article_id ):
        rec = module.BlogEntry[article_id]
        rec.delete()
        return request.make_response_object(self)  # reload


class BlogModule(PonyOrmModule):

    def __init__( self ):
        PonyOrmModule.__init__(self, MODULE_NAME)
        self.article_module = article.module

    def init_phase2( self ):
        self.Article = self.article_module.Article
        self.BlogEntry = self.make_inherited_entity('BlogEntry', self.Article,
                                                    created_at=Required(datetime))

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
            return request.make_response_object(Blog(self.get_blog_path()))
        return PonyOrmModule.run_command(self, request, command_id)

    def get_blog_path( self ):
        return self.make_path(object='blog')


module = BlogModule()
