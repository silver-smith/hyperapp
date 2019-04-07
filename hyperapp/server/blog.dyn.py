from datetime import datetime
import logging
import codecs

from pony.orm import db_session, flush, desc, Required, Optional, Set

from hyperapp.common.htypes import ref_t
from hyperapp.common.util import dt_naive_to_utc, single
from hyperapp.common.ref import ref_repr, ref_list_repr
from hyperapp.common.list_object import rows2fetched_chunk
from hyperapp.server.util import utcnow
from . import htypes
from .ponyorm_module import PonyOrmModule

log = logging.getLogger(__name__)


MODULE_NAME = 'blog'
BLOG_SERVICE_ID = 'blog'


class BlogService(object):

    def __init__(self, ref_storage, proxy_factory):
        self._ref_storage = ref_storage
        self._proxy_factory = proxy_factory
        self._subscriptions = {}  # blog id -> service ref set

    def get_self(self):
        return self

    def rpc_fetch_blog_contents(self, request, blog_id, from_key):
        all_items = self.fetch_blog_contents(blog_id)
        if from_key is None:
            idx = 0
        else:
            idx = single(idx for idx, item in enumerate(all_items)
                         if item.id == from_key) + 1
        chunk = htypes.blog.blog_chunk(
            from_key=from_key,
            items=all_items[idx:],
            eof=True,
            )
        return request.make_response_result(chunk=chunk)

    @db_session
    def fetch_blog_contents(self, blog_id):
        # blog_id is ignored now
        return list(map(self.rec2item, this_module.BlogEntry.select().filter(blog_id=blog_id)))

    @classmethod
    def rec2item(cls, rec):
        ref_list = map(cls.rec2ref, rec.refs.select().order_by(this_module.ArticleRef.id))
        return htypes.blog.blog_item(
            id=rec.id,
            created_at=dt_naive_to_utc(rec.created_at),
            title=rec.title,
            text=rec.text,
            ref_list=list(ref_list),
            )

    @staticmethod
    def rec2ref(rec):
        return htypes.blog.article_ref(
            id=rec.id,
            title=rec.title,
            ref=ref_t(rec.ref_hash_algorithm, rec.ref_hash),
            )

    @db_session
    def rpc_create_article(self, request, blog_id, title, text):
        article = this_module.BlogEntry(
            blog_id=blog_id,
            created_at=utcnow(),
            title=title,
            text=text,
            )
        flush()
        log.info('Article#%d is created for blog %r', article.id, blog_id)
        subscribed_service_ref_list = self._subscriptions.get(blog_id, [])
        log.debug("Subscriptions for %r: %s", blog_id, ref_list_repr(subscribed_service_ref_list))
        for service_ref in subscribed_service_ref_list:
            log.info("Sending 'article_added' notification to %s", ref_repr(service_ref))
            proxy = self._proxy_factory.from_ref(service_ref)
            proxy.article_added(blog_id, self.rec2item(article))
        return request.make_response_result(blog_item=self.rec2item(article))

    def _get_article(self, blog_id, article_id):
        article = this_module.BlogEntry.get(id=article_id)
        if article and article.blog_id == blog_id:
            return article
        else:
            raise htypes.blog.unknown_article_error(blog_id, article_id)

    @db_session
    def rpc_save_article(self, request, blog_id, article_id, title, text):
        article = self._get_article(blog_id, article_id)
        article.title = title
        article.text = text
        log.info('Article#%d is saved: %r/%r', article_id, title, text)
        subscribed_service_ref_list = self._subscriptions.get(blog_id, [])
        log.debug("Subscriptions for %r: %s", blog_id, ref_list_repr(subscribed_service_ref_list))
        for service_ref in subscribed_service_ref_list:
            log.info("Sending 'article_changed' notification to %s", ref_repr(service_ref))
            proxy = self._proxy_factory.from_ref(service_ref)
            proxy.article_changed(blog_id, self.rec2item(article))

    @db_session
    def rpc_delete_article(self, request, blog_id, article_id):
        article = self._get_article(blog_id, article_id)
        article.delete()
        log.info('Article#%d is deleted.', article_id)
        subscribed_service_ref_list = self._subscriptions.get(blog_id, [])
        log.debug("Subscriptions for %r: %s", blog_id, ref_list_repr(subscribed_service_ref_list))
        for service_ref in subscribed_service_ref_list:
            log.info("Sending 'article_deleted' notification to %s", ref_repr(service_ref))
            proxy = self._proxy_factory.from_ref(service_ref)
            proxy.article_deleted(blog_id, article_id)

    @db_session
    def rpc_add_ref(self, request, blog_id, article_id, title, ref):
        article = self._get_article(blog_id, article_id)
        rec = this_module.ArticleRef(
            article=article,
            title=title,
            ref_hash_algorithm=ref.hash_algorithm,
            ref_hash=ref.hash,
            )
        self._ref_storage.store_ref(ref)
        flush()  # make rec.id
        log.info('Blog %r article#%d ref#%d %s is added with title %r', blog_id, article.id, rec.id, ref_repr(ref), title)
        return request.make_response_result(ref_id=rec.id)

    @db_session
    def rpc_update_ref(self, request, blog_id, article_id, ref_id, title, ref):
        rec = this_module.ArticleRef[ref_id]
        rec.title = title
        rec.ref = ref
        self._ref_storage.store_ref(ref)
        log.info('Blog %r article#%d ref#%d is updated to %s, title %r', blog_id, article_id, rec.id, ref_repr(ref), title)

    @db_session
    def rpc_delete_ref(self, request, blog_id, article_id, ref_id):
        this_module.ArticleRef[ref_id].delete()
        log.info('Article ref#%d is deleted', ref_id)

    def rpc_subscribe(self, request, blog_id_list, service_ref):
        for blog_id in blog_id_list:
            blog_service_ref_set = self._subscriptions.setdefault(blog_id, set())
            blog_service_ref_set.add(service_ref)
            log.debug('Add subscription to %r for %s', blog_id, ref_repr(service_ref))


class ThisModule(PonyOrmModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        self._blog_service = BlogService(services.ref_storage, services.proxy_factory)
        iface_type_ref = services.type_resolver.reverse_resolve(htypes.blog.blog_service_iface)
        service = htypes.hyper_ref.service(BLOG_SERVICE_ID, iface_type_ref)
        self._blog_service_ref = service_ref = services.ref_registry.register_object(service)
        services.blog_service_ref = service_ref
        services.service_registry.register(service_ref, self._blog_service.get_self)

    def init_phase_2(self, services):
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
            ref_hash_algorithm=Required(str),
            ref_hash=Required(bytes),
            )
        self.BlogEntry = self.make_inherited_entity(
            'BlogEntry', self.Article,
            blog_id=Required(str),
            created_at=Required(datetime),
            )

    def init_phase_3(self, services):
        blog = htypes.blog.blog(
            blog_service_ref=self._blog_service_ref,
            blog_id='test-blog',
            current_article_id=None,
            )
        blog_ref = services.ref_registry.register_object(blog)
        services.management_ref_list.add_ref('blog', blog_ref)
