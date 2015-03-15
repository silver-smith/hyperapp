from datetime import datetime
from pony.orm import db_session, desc, Required, Set
from ponyorm_module import PonyOrmModule
from util import utcnow, str2id
from object import ListObject, Command, Element, Column
from module import ModuleCommand
from iface import ListIface
import article


MODULE_NAME = 'blog'


class BlogEntry(article.Article):

    @db_session
    def __init__( self, path, entry_id, mode=article.Article.mode_view ):
        if entry_id is None:
            article_id = None
        else:
            entry_rec = module.BlogEntry[entry_id]
            article_id = entry_rec.article.id
        article.Article.__init__(self, path, article_id, mode)
        self.entry_id = entry_id

    @classmethod
    def make( cls, entry_id, mode=article.Article.mode_view ):
        return cls(module.make_path(object='entry', entry_id=entry_id), entry_id, mode)

    @classmethod
    def from_path( cls, path ):
        entry_id = path['entry_id']
        return cls(path, entry_id)

    def do_save( self, text ):
        with db_session:
            if self.entry_id is not None:
                entry_rec = module.BlogEntry[self.entry_id]
                article_rec = entry_rec.article
            else:
                article_rec = None
            article_rec = self.save_article(article_rec, text)
            if self.entry_id is None:
                entry_rec = module.BlogEntry(
                    article=article_rec,
                    created_at=utcnow())
        print 'Blog entry is saved, entry id =', entry_rec.id, ' article_id =', article_rec.id
        return dict(self.path, entry_id=entry_rec.id)


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
        return request.make_response_object(BlogEntry.make(entry_id=None, mode=BlogEntry.mode_edit))

    @db_session
    def get_all_elements( self ):
        return map(self.rec2element, module.BlogEntry.select().order_by(desc(module.BlogEntry.created_at)))

    def rec2element( self, rec ):
        commands = [Command('open', 'Open', 'Open blog entry'),
                    Command('delete', 'Delete', 'Delete blog entry', 'Del'),
                    ]
        return Element(rec.id, [rec.id, rec.created_at], commands)

    def run_element_command( self, request, command_id, element_key ):
        if command_id == 'open':
            entry_id = element_key
            return request.make_response_object(BlogEntry.make(entry_id=element_key))
        if command_id == 'delete':
            return self.run_element_command_delete(request, element_key)
        return ListObject.run_element_command(self, request, command_id, element_key)

    @db_session
    def run_element_command_delete( self, request, entry_id ):
        rec = module.BlogEntry[entry_id]
        rec.article.delete()
        rec.delete()
        return request.make_response_object(self)  # reload


class BlogModule(PonyOrmModule):

    def __init__( self ):
        PonyOrmModule.__init__(self, MODULE_NAME)
        self.article_module = article.module
        self.article_module.add_article_fields(blog=Set('BlogEntry'))

    def init_phase2( self ):
        self.Article = self.article_module.Article
        self.BlogEntry = self.make_entity('BlogEntry',
                                          article=Required(self.Article),
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
            return request.make_response_object(BlogEntry.make(entry_id=None))
        if command_id == 'open_blog':
            return request.make_response_object(Blog(self.make_path(object='blog')))
        return PonyOrmModule.run_command(self, request, command_id)


module = BlogModule()
