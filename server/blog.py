from datetime import datetime
from pony.orm import db_session, Required, Set
from ponyorm_module import PonyOrmModule
from util import utcnow
from module import ModuleCommand
import article


MODULE_NAME = 'blog'


class BlogEntry(article.Article):

    def do_save( self, text ):
        ident = self.path.rsplit('/', 1)[-1]
        if ident == 'new':
            entry_id = None
        else:
            entry_id = int(ident)
        with db_session:
            if entry_id is not None:
                entry_rec = module.BlogEntry[entry_id]
                article_id = entry_rec.article.id
            else:
                article_id = None
            article_rec = self.save_article(article_id, text)
            if entry_id is None:
                entry_rec = module.BlogEntry(
                    article=article_rec,
                    created_at=utcnow())
        print 'Blog entry is saved, entry id =', entry_rec.id, ' article_id =', article_rec.id
        return '/blog_entry/%d' % entry_rec.id


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
        return [ModuleCommand('create', 'Create entry', 'Create new blog entry', 'Alt+B', self.name)]

    def run_command( self, command_id ):
        if command_id == 'create':
            return BlogEntry('/blog_entry/new')
        assert False, repr(command_id)  # Unsupported command


module = BlogModule()
