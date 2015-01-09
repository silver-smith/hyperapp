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
    def get_article_id( self ):
        entry_id = str2id(self.path.split('/')[-1])
        if entry_id == None:
            return None
        entry_rec = module.BlogEntry[entry_id]
        return entry_rec.article.id

    def do_save( self, text ):
        entry_id = str2id(self.path.split('/')[-1])
        with db_session:
            if entry_id is not None:
                entry_rec = module.BlogEntry[entry_id]
                article_rec = entry_rec.article
            else:
                article_rec = None
            article_rec = self.save_article(article_rec, text)
            if entry_id is None:
                entry_rec = module.BlogEntry(
                    article=article_rec,
                    created_at=utcnow())
        print 'Blog entry is saved, entry id =', entry_rec.id, ' article_id =', article_rec.id
        return '/blog_entry/%d' % entry_rec.id


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

    def run_command( self, command_id, request ):
        if command_id == 'add':
            return self.run_command_add(request)
        return ListObject.run_command(self, command_id, request)

    def run_command_add( self, request ):
        return BlogEntry('/blog_entry/new')

    @db_session
    def get_all_elements( self ):
        return map(self.rec2element, module.BlogEntry.select().order_by(desc(module.BlogEntry.created_at)))

    def rec2element( self, rec ):
        commands = [Command('open', 'Open', 'Open blog entry'),
                    Command('delete', 'Delete', 'Delete blog entry', 'Del'),
                    ]
        return Element(rec.id, [rec.id, rec.created_at], commands)

    def run_element_command( self, command_id, element_key ):
        if command_id == 'open':
            entry_id = element_key
            return BlogEntry('/blog_entry/%s' % entry_id)
        if command_id == 'delete':
            return self.run_element_command_delete(element_key)
        return ListObject.run_element_command(self, command_id, element_key)

    @db_session
    def run_element_command_delete( self, entry_id ):
        module.BlogEntry[entry_id].delete()
        return self  # reload


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

    def get_commands( self ):
        return [
            ModuleCommand('create', 'Create entry', 'Create new blog entry', None, self.name),
            ModuleCommand('open_blog', 'Blog', 'Open blog', 'Alt+B', self.name),
            ]

    def run_command( self, command_id ):
        if command_id == 'create':
            return BlogEntry('/blog_entry/new')
        if command_id == 'open_blog':
            return Blog('/blog/')
        assert False, repr(command_id)  # Unsupported command


module = BlogModule()
