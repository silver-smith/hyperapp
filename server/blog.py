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

    @db_session
    def get_all_elements( self ):
        return map(self.rec2element, module.BlogEntry.select().order_by(desc(module.BlogEntry.created_at)))

    def rec2element( self, rec ):
        commands = [Command('open', 'Open', 'Open blog entry')]
        return Element(rec.id, [rec.id, rec.created_at], commands)

    def run_element_command( self, command_id, element_key ):
        if command_id == 'open':
            entry_id = element_key
            return BlogEntry('/blog_entry/%s' % entry_id)
        return ListObject.run_element_command(self, command_id, element_key)


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
