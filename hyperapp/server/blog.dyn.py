from datetime import datetime
import logging
import codecs

from pony.orm import db_session, flush, desc, Required, Optional, Set

from ..common.interface import core as core_types
from ..common.interface import hyper_ref as href_types
from ..common.interface import blog as blog_types
from ..common.list_object import rows2fetched_chunk
from .util import utcnow, path_part_to_str
from .ponyorm_module import PonyOrmModule

log = logging.getLogger(__name__)


MODULE_NAME = 'blog'
BLOG_SERVICE_ID = 'blog'


class BlogService(object):

    def rpc_fetch_blog_contents(self, request, blog_id, fetch_request):
        all_rows = self.fetch_blog_contents(blog_id)
        chunk = rows2fetched_chunk('id', all_rows, fetch_request, blog_types.blog_chunk)
        return request.make_response_result(chunk=chunk)

    @db_session
    def fetch_blog_contents(self, blog_id):
        # blog_id is ignored now
        return list(map(self.rec2row, this_module.BlogEntry.select()))

    @classmethod
    def rec2row(cls, rec):
        ref_list = map(cls.rec2ref, rec.refs.select().order_by(this_module.ArticleRef.id))
        return blog_types.blog_row(
            id=rec.id,
            created_at=rec.created_at,
            title=rec.title,
            text=rec.text,
            ref_list=list(ref_list),
            )

    @staticmethod
    def rec2ref(rec):
        return blog_types.article_ref(
            id=rec.id,
            title=rec.title,
            ref=rec.ref,
            )

    @db_session
    def rpc_create_article(self, request, blog_id, title, text):
        article = this_module.BlogEntry(
            created_at=utcnow(),
            title=title,
            text=text,
            )
        flush()
        log.info('Article#%d is created', article.id)
        return request.make_response_result(blog_row=self.rec2row(article))

    def _get_article(self, blog_id, article_id):
        article = this_module.BlogEntry.get(id=article_id)
        if article:
            return article
        else:
            raise blog_types.unknown_article_error(article_id)

    @db_session
    def rpc_save_article(self, request, blog_id, article_id, title, text):
        article = self._get_article(blog_id, article_id)
        article.title = title
        article.text = text
        log.info('Article#%d is saved: %r/%r', article_id, title, text)

    @db_session
    def rpc_add_ref(self, request, blog_id, article_id, title, ref):
        article = self._get_article(blog_id, article_id)
        rec = this_module.ArticleRef(
            article=article,
            title=title,
            ref=ref,
            )
        flush()  # make rec.id
        log.info('Article ref#%d %r is is added: %s', rec.id, title, codecs.encode(rec.ref, 'hex'))
        return request.make_response_result(ref_id=rec.id)

    @db_session
    def rpc_update_ref(self, request, blog_id, article_id, ref_id, title, ref):
        rec = this_module.ArticleRef[ref_id]
        rec.title = title
        rec.ref = ref
        log.info('Article ref#%d is updated to %r: %s', rec.id, title, codecs.encode(rec.ref, 'hex'))

    @db_session
    def rpc_delete_ref(self, request, ref_id):
        this_module.ArticleRef[ref_id].delete()
        log.info('Article ref#%d is deleted', ref_id)


class ThisModule(PonyOrmModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)

    def init_phase2(self, services):
        self.Article = self.make_entity(
            'Article',
            title=Required(str),
            text=Optional(str),
            refs=Set('ArticleRef'),
            )
        self.ArticleRef = self.make_entity(
            'ArticleRef',
            article=Required(self.Article),
            title=Required(str),
            ref=Required(bytes),
            )
        self.BlogEntry = self.make_inherited_entity(
            'BlogEntry', self.Article,
            created_at=Required(datetime),
            )

    def init_phase3(self, services):
        service = href_types.service(BLOG_SERVICE_ID, ['blog', 'blog_service_iface'])
        service_ref = services.ref_registry.register_object(service)
        services.service_registry.register(service_ref, BlogService)

        blog = blog_types.blog_ref(
            blog_service_ref=service_ref,
            blog_id='test-blog',
            current_article_id=None,
            )
        blog_ref = services.ref_registry.register_object(blog)
        services.management_ref_list.add_ref('blog', blog_ref)

#    def get_commands(self):
#        return [
#            ModuleCommand('create', 'Create entry', 'Create new blog entry', None, self.name),
#            ModuleCommand('open_blog', 'Blog', 'Open blog', 'Alt+B', self.name),
#            ]

#    def run_command(self, request, command_id):
#        if command_id == 'create':
#            return request.make_response_object(BlogEntry())
#        if command_id == 'open_blog':
#            return request.make_response_object(Blog())
#        return PonyOrmModule.run_command(self, request, command_id)
