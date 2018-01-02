from datetime import datetime
import logging
from pony.orm import db_session, commit, desc, Required, Set
from ..common.diff import SimpleDiff
from ..common.list_object import ListDiff
from ..common.interface import core as core_types
from ..common.interface import hyper_ref as href_types
from ..common.interface import blog as blog_types
from .ponyorm_module import PonyOrmModule
from .util import utcnow, path_part_to_str
from .command import command
from .object import Object, subscription
from .module import ModuleCommand
from .list_object import rows2fetched_chunk

log = logging.getLogger(__name__)


MODULE_NAME = 'blog'


class BlogService(Object):

    iface = blog_types.blog_service_iface
    class_name = 'service'

    @classmethod
    def get_path(cls):
        return this_module.make_path(cls.class_name)

    @classmethod
    def resolve(cls, path):
        path.check_empty()
        return cls()

    @command('fetch_blog_contents')
    def command_fetch_blog_contents(self, request):
        all_rows = self.fetch_blog_contents(request.params.blog_id)
        chunk = rows2fetched_chunk('id', all_rows, request.params.fetch_request, blog_types.blog_chunk)
        return request.make_response_result(chunk=chunk)

    @db_session
    def fetch_blog_contents(self, blog_id):
        # blog_id is ignored now
        return list(map(self.rec2element, this_module.BlogEntry.select()))

    @classmethod
    def rec2element(cls, rec):
        ref_list = map(cls.rec2ref, rec.refs.select().order_by(this_module.ArticleRef.id))
        return blog_types.blog_row(
            id=rec.id,
            created_at=rec.created_at,
            title='Article #%d' % rec.id,
            text=rec.text,
            ref_list=list(ref_list),
            )

    @staticmethod
    def rec2ref(rec):
        return blog_types.article_ref(
            id=rec.id,
            title=rec.title,
            href=href_types.href('sha256', rec.href),
            )

    @command('update_ref')
    @db_session
    def command_update_ref(self, request):
        rec = this_module.ArticleRef[request.params.ref_id]
        rec.href = request.params.ref.hash
        log.info('Article ref#%d is updated to %s', rec.id, rec.href.decode())


class ThisModule(PonyOrmModule):

    def __init__(self, services):
        PonyOrmModule.__init__(self, MODULE_NAME)

    def init_phase2(self):
        self.Article = self.make_entity(
            'Article',
            text=Required(str),
            refs=Set('ArticleRef'),
            )
        self.ArticleRef = self.make_entity(
            'ArticleRef',
            article=Required(self.Article),
            title=Required(str),
            href=Required(bytes),
            )
        self.BlogEntry = self.make_inherited_entity(
            'BlogEntry', self.Article,
            created_at=Required(datetime),
            )

    def resolve(self, iface, path):
        name = path.pop_str()
        if name == BlogService.class_name:
            return BlogService.resolve(path)
        path.raise_not_found()

    def get_commands(self):
        return [
            ModuleCommand('create', 'Create entry', 'Create new blog entry', None, self.name),
            ModuleCommand('open_blog', 'Blog', 'Open blog', 'Alt+B', self.name),
            ]

    def run_command(self, request, command_id):
        if command_id == 'create':
            return request.make_response_object(BlogEntry())
        if command_id == 'open_blog':
            return request.make_response_object(Blog())
        return PonyOrmModule.run_command(self, request, command_id)
