from datetime import datetime
import logging
from pony.orm import db_session, commit, desc, Required, Set
from ..common.interface.blog import blog_entry_iface, blog_iface
from .ponyorm_module import PonyOrmModule
from .util import utcnow, path_part_to_str
from .command import command
from .object import SmallListObject, subscription
from .module import ModuleCommand
from . import article

log = logging.getLogger(__name__)


MODULE_NAME = 'blog'


class BlogEntry(article.Article):

    iface = blog_entry_iface
    objimpl_id = 'proxy.text'

    def get_path( self ):
        return module.make_path(self.class_name, path_part_to_str(self.article_id, none_str='new'))

    @command('parent')    
    def command_parent( self, request ):
        return request.make_response_object(Blog())

    @db_session
    def do_save( self, request, text ):
        if self.article_id is not None:
            entry_rec = module.BlogEntry[self.article_id]
            entry_rec.text = text
            is_insertion = False
        else:
            entry_rec = module.BlogEntry(
                text=text,
                created_at=utcnow())
            is_insertion = True
        commit()
        self.article_id = entry_rec.id  # now may have new get_path()
        log.info('Blog entry is saved, blog entry id = %r', self.article_id)
        subscription.distribute_update(self.iface, self.get_path(), text)
        if is_insertion:
            diff = Blog.Diff_insert_one(entry_rec.id, Blog.rec2element(entry_rec))
            subscription.distribute_update(blog_iface, Blog.get_path(), diff)
        return request.make_response_result(new_path=self.get_path())


class Blog(SmallListObject):

    iface = blog_iface
    objimpl_id = 'proxy_list'
    class_name = 'blog'
    default_sort_column_id = 'id'

    @classmethod
    def resolve( cls, path ):
        return cls()

    def __init__( self ):
        SmallListObject.__init__(self)

    @classmethod
    def get_path( cls ):
        return module.make_path(cls.class_name)

    @command('add')
    def command_add( self, request ):
        return request.make_response_object(BlogEntry(mode=BlogEntry.mode_edit))

    @db_session
    def fetch_all_elements( self ):
        return list(map(self.rec2element, module.BlogEntry.select().order_by(desc(module.BlogEntry.created_at))))

    @classmethod
    def rec2element( cls, rec ):
        commands = [cls.command_open, cls.command_delete]
        return cls.Element(cls.Row(rec.id, rec.created_at), commands)

    @command('open', kind='element', is_default_command=True)
    def command_open( self, request ):
        article_id = request.params.element_key
        return request.make_response_object(BlogEntry(article_id))
    
    @command('delete', kind='element')
    @db_session
    def command_delete( self, request ):
        article_id = request.params.element_key
        module.BlogEntry[article_id].delete()
        diff = self.Diff_delete(article_id)
        subscription.distribute_update(self.iface, self.get_path(), diff)


class BlogModule(PonyOrmModule):

    def __init__( self ):
        PonyOrmModule.__init__(self, MODULE_NAME)
        self.article_module = article.module

    def init_phase2( self ):
        self.Article = self.article_module.Article
        self.BlogEntry = self.make_inherited_entity('BlogEntry', self.Article,
                                                    created_at=Required(datetime))
        BlogEntry.register_class(self.BlogEntry)

    def resolve( self, iface, path ):
        objname = path.pop_str()
        if objname == BlogEntry.class_name:
            return BlogEntry.resolve(path)
        if objname == Blog.class_name:
            return Blog.resolve(path)
        path.raise_not_found()

    def get_commands( self ):
        return [
            ModuleCommand('create', 'Create entry', 'Create new blog entry', None, self.name),
            ModuleCommand('open_blog', 'Blog', 'Open blog', 'Alt+B', self.name),
            ]

    def run_command( self, request, command_id ):
        if command_id == 'create':
            return request.make_response_object(BlogEntry())
        if command_id == 'open_blog':
            return request.make_response_object(Blog())
        return PonyOrmModule.run_command(self, request, command_id)


module = BlogModule()
