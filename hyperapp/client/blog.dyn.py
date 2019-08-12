import logging
import asyncio
from collections import OrderedDict
import uuid
import abc

from hyperapp.common.htypes import tInt, tDateTime, resource_key_t
from hyperapp.client.module import ClientModule
from hyperapp.client.command import command
from . import htypes
from .column import Column
from .list_object import ListObject
from .text_object import TextObject
from .record_object import RecordObject
#from .form import FormObject, FormView
#from . import object_selector

log = logging.getLogger(__name__)


class BlogObserver(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def article_added(self, blog_id, article):
        pass

    @abc.abstractmethod
    def article_changed(self, blog_id, article):
        pass

    @abc.abstractmethod
    def article_deleted(self, blog_id, article_id):
        pass


class BlogObject(ListObject, BlogObserver):

    @classmethod
    async def from_state(cls, state, ref_registry, blog_service_factory):
        blog_service = await blog_service_factory(state.blog_service_ref)
        return cls(ref_registry, blog_service, state.blog_id)

    def __init__(self, ref_registry, blog_service, blog_id):
        ListObject.__init__(self)
        self._ref_registry = ref_registry
        self._blog_service = blog_service
        self._blog_id = blog_id
        log.debug('Created %r', self)

    def __repr__(self):
        return '<BlogObject#%d>' % id(self)

    def __del__(self):
        log.debug('Deleted %r', self)

    def get_title(self):
        return self._blog_id

    def observers_arrived(self):
        asyncio.ensure_future(self._blog_service.add_observer(self._blog_id, self))

    def observers_gone(self):
        self._blog_service.remove_observer(self._blog_id, self)

    def get_columns(self):
        return [
            Column('id', type=tInt, is_key=True),
            Column('created_at', type=tDateTime),
            Column('title'),
            ]

    async def fetch_items(self, from_key):
        chunk = await self._blog_service.fetch_blog_contents(self._blog_id, from_key)
        self._distribute_fetch_results(chunk.items)
        if chunk.eof:
            self._distribute_eof()

    def article_added(self, blog_id, article):
        diff = ListDiff.add_one(self._row_to_element(article))
        self._notify_diff_applied(diff)

    def article_changed(self, blog_id, article):
        diff = ListDiff.replace(article.id, self._row_to_element(article))
        self._notify_diff_applied(diff)

    def article_deleted(self, blog_id, article_id):
        diff = ListDiff.delete(article_id)
        self._notify_diff_applied(diff)

    def process_diff(self, diff):
        assert isinstance(diff, ListDiff), repr(diff)
        log.info('-- BlogObject.process_diff self=%r diff=%r', id(self), diff)

    @command('open', kind='element')
    async def command_open(self, item_id):
        return (await self._open_article(article_id=item_id, mode='view'))

    @command('delete', kind='element')
    async def command_delete(self, item_id):
        await self._blog_service.delete_article(self._blog_id, article_id=item_id)

    @command('add')
    async def command_add(self):
        article_id = await self._blog_service.create_article(self._blog_id, 'Untitled', '')
        return (await self._open_article(article_id, mode='edit'))

    async def _open_article(self, article_id, mode):
        return htypes.blog.blog_article(self._blog_service.ref, self._blog_id, article_id)


class BlogArticle(RecordObject):

    @classmethod
    async def from_state(cls, state, blog_service_factory):
        blog_service = await blog_service_factory(state.blog_service_ref)
        item = await blog_service.get_blog_item(state.blog_id, state.article_id)
        return cls(blog_service, state.blog_id, item)

    def __init__(self, blog_service, blog_id, item):
        super().__init__()
        self._blog_service = blog_service
        self._blog_id = blog_id
        self._item = item

    def get_title(self):
        return self._item.title

    def get_fields(self):
        return OrderedDict([
            ('title', htypes.text.text(self._item.title)),
            ('contents', htypes.text.wiki_text(self._item.text, self._item.ref_list)),
            ])

    @command('parent')
    async def command_parent(self):
        blog_service_ref = self._blog_service.to_ref()
        return (await this_module.open_blog(blog_service_ref, self._blog_id, current_article_id=self._article_id))

    @command('refs')
    async def command_refs(self):
        blog_service_ref = self._blog_service.to_ref()
        object = htypes.blog.blog_article_ref_list(blog_service_ref, self._blog_id, self._article_id, selected_ref_id=None)
        ref = self._ref_registry.register_object(object)
        return (await self._handle_resolver.resolve(ref))

    @command('save')
    async def command_save(self):
        title = self._fields['title'].line
        text = self._fields['text'].text
        await self._blog_service.save_article(self._blog_id, self._article_id, title, text)


# class BlogArticleContents(TextObject):

#     impl_id = 'blog_article_contents'

#     @classmethod
#     def from_state(cls, state, handle_resolver):
#         return cls(handle_resolver, state.text, state.ref_list)

#     def __init__(self, handle_resolver, text, ref_list):
#         super().__init__(text)
#         self._handle_resolver = handle_resolver
#         self._ref_list = ref_list

#     def get_title(self):
#         return None

#     def get_state(self):
#         return htypes.blog.blog_article_text(self.impl_id, self._text, self._ref_list)

#     async def open_ref(self, id):
#         log.info('Opening ref: %r', id)
#         id2ref = {ref.id: ref.ref for ref in self._ref_list}
#         ref = id2ref.get(int(id))
#         if not ref:
#             log.warning('ref is missing: %r', id)
#             return
#         return (await self._handle_resolver.resolve(ref))


# class ArticleRefListObject(ListObject):

#     impl_id = 'article-ref-list'

#     @classmethod
#     async def from_state(cls, state, ref_registry, blog_service_factory, handle_resolver):
#         blog_service = await blog_service_factory(state.blog_service_ref)
#         return cls(ref_registry, handle_resolver, blog_service, state.blog_id, state.article_id)

#     def __init__(self, ref_registry, handle_resolver, blog_service, blog_id, article_id):
#         ListObject.__init__(self)
#         self._ref_registry = ref_registry
#         self._handle_resolver = handle_resolver
#         self._blog_service = blog_service
#         self._blog_id = blog_id
#         self._article_id = article_id
#         self._id2ref = {}

#     def get_state(self):
#         return htypes.blog.article_ref_list_object(self.impl_id, self._blog_service.to_ref(), self._blog_id, self._article_id)

#     def get_title(self):
#         return 'refs for %s:%d' % (self._blog_id, self._article_id)

#     def pick_current_refs(self):
#         return []

#     def get_columns(self):
#         return [
#             Column('id', type=tInt, is_key=True),
#             Column('title'),
#             Column('ref'),
#             ]

#     def get_key_column_id(self):
#         return 'id'

#     async def fetch_items(self, from_key):
#         ref_list = await self._blog_service.get_article_ref_list(self._blog_id, self._article_id)
#         self._id2ref.update({item.id: item.ref for item in ref_list})
#         self._distribute_fetch_results(ref_list)
#         self._distribute_eof()

#     async def get_ref_handle(self, id):
#         ref = self._id2ref[id]
#         return (await self._handle_resolver.resolve(ref))

#     @command('parent')
#     async def command_parent(self):
#         return (await this_module.open_article(self._blog_service, self._blog_id, self._article_id))

#     @command('open', kind='element')
#     async def command_open(self, item_id):
#         return (await self.get_ref_handle(item_id))

#     @command('add')
#     async def command_add(self):
#         blog_service_ref = self._blog_service.to_ref()
#         article_ref_list_object = htypes.blog.blog_article_ref_list(blog_service_ref, self._blog_id, self._article_id)
#         target_ref = self._ref_registry.register_object(article_ref_list_object)
#         target_handle = await self._handle_resolver.resolve(target_ref)
#         callback = htypes.blog.selector_callback(self._blog_service.to_ref(), self._blog_id, self._article_id)
#         object = htypes.object_selector.object_selector_object('object_selector', callback)
#         return htypes.object_selector.object_selector_view('object_selector', object, target_handle)

#     @command('change', kind='element')
#     async def command_change(self, item_id):
#         target_handle = await self.get_ref_handle(item_id)
#         callback = htypes.blog.selector_callback(self._blog_service.to_ref(), self._blog_id, self._article_id, item_id)
#         object = htypes.object_selector.object_selector_object('object_selector', callback)
#         return htypes.object_selector.object_selector_view('object_selector', object, target_handle)

#     @command('delete', kind='element')
#     async def command_delete(self, item_id):
#         await self._blog_service.delete_ref(self._blog_id, self._article_id, item_id)


# class SelectorCallback(object):

#     @classmethod
#     async def from_data(cls, state, ref_registry, blog_service_factory, handle_resolver):
#         blog_service = await blog_service_factory(state.blog_service_ref)
#         return cls(ref_registry, handle_resolver, blog_service, state.blog_id, state.article_id, state.ref_id)

#     def __init__(self, ref_registry, handle_resolver, blog_service, blog_id, article_id, ref_id):
#         self._ref_registry = ref_registry
#         self._handle_resolver = handle_resolver
#         self._blog_service = blog_service
#         self._blog_id = blog_id
#         self._article_id = article_id
#         self._ref_id = ref_id

#     async def set_ref(self, title, ref):
#         if self._ref_id is not None:
#             await self._blog_service.update_ref(self._blog_id, self._article_id, self._ref_id, title, ref)
#             ref_id = self._ref_id
#         else:
#             ref_id = await self._blog_service.add_ref(self._blog_id, self._article_id, title, ref)
#         blog_service_ref = self._blog_service.to_ref()
#         object = htypes.blog.blog_article_ref_list(blog_service_ref, self._blog_id, self._article_id, ref_id)
#         ref = self._ref_registry.register_object(object)
#         return (await self._handle_resolver.resolve(ref))

#     def to_data(self):
#         return htypes.blog.selector_callback(self._blog_service.to_ref(), self._blog_id, self._article_id, self._ref_id)
    

class BlogNotification(object):

    def __init__(self, blog_service):
        self._blog_service = blog_service

    def rpc_article_added(self, request, blog_id, article):
        self._blog_service.article_added(blog_id, article)

    def rpc_article_changed(self, request, blog_id, article):
        self._blog_service.article_changed(blog_id, article)

    def rpc_article_deleted(self, request, blog_id, article_id):
        self._blog_service.article_deleted(blog_id, article_id)

    def get_self(self):
        return self


class BlogService(object):

    @classmethod
    async def from_data(cls, type_resolver, ref_registry, service_registry, proxy_factory, service_ref):
        proxy = await proxy_factory.from_ref(service_ref)
        return cls(type_resolver, ref_registry, service_registry, proxy)

    def __init__(self, type_resolver, ref_registry, service_registry, proxy):
        self._type_resolver = type_resolver
        self._ref_registry = ref_registry
        self._service_registry = service_registry
        self._proxy = proxy
        self._items_cache = {}  # (blog_id, article_id) -> blog_item, already fetched items
        self._blog_id_to_observer_set = {}
        self._subscribed_to_blog_id_set = set()
        self._notification = BlogNotification(self)

    @property
    def ref(self):
        return self._proxy.service_ref

    async def add_observer(self, blog_id, observer):
        log.info('Blog service: add observer for %r: %r', blog_id, observer)
        observer_set = self._blog_id_to_observer_set.setdefault(blog_id, set())
        observer_set.add(observer)
        await self._ensure_subscribed(blog_id)

    def remove_observer(self, blog_id, observer):
        log.info('Blog service: remove observer for %r: %r', blog_id, observer)
        observer_set = self._blog_id_to_observer_set[blog_id]
        observer_set.remove(observer)

    async def _ensure_subscribed(self, blog_id):
        if blog_id in self._subscribed_to_blog_id_set:
            return
        service_id = str(uuid.uuid4())
        iface_type_ref = self._type_resolver.reverse_resolve(htypes.blog.blog_notification_iface)
        service = htypes.hyper_ref.service(service_id, iface_type_ref)
        service_ref = self._ref_registry.register_object(service)
        self._service_registry.register(service_ref, self._notification.get_self)
        await self._proxy.subscribe([blog_id], service_ref)

    def article_added(self, blog_id, article):
        for observer in  self._blog_id_to_observer_set.get(blog_id, []):
            log.info("Blog: notifying observer for 'article_added': %r", observer)
            observer.article_added(blog_id, article)

    def article_changed(self, blog_id, article):
        for observer in  self._blog_id_to_observer_set.get(blog_id, []):
            log.info("Blog: notifying observer for 'article_changed': %r", observer)
            observer.article_changed(blog_id, article)

    def article_deleted(self, blog_id, article_id):
        for observer in  self._blog_id_to_observer_set.get(blog_id, []):
            log.info("Blog: notifying observer for 'article_deleted': %r", observer)
            observer.article_deleted(blog_id, article_id)

    async def fetch_blog_contents(self, blog_id, from_key=None):
        result = await self._proxy.fetch_blog_contents(blog_id, from_key)
        self._items_cache.update({(blog_id, item.id): item for item in result.chunk.items})
        return result.chunk

    async def get_blog_item(self, blog_id, article_id):
        item = self._items_cache.get((blog_id, article_id))
        if not item:
            await self.fetch_blog_contents(blog_id)
            item = self._items_cache.get((blog_id, article_id))
            assert item, repr((blog_id, article_id))  # expecting it to be fetched now
        return item

    async def create_article(self, blog_id, title, text):
        result = await self._proxy.create_article(blog_id, title, text)
        item = result.blog_item
        self._items_cache[(blog_id, item.id)] = item
        return item.id

    async def save_article(self, blog_id, article_id, title, text):
        await self._proxy.save_article(blog_id, article_id, title, text)

    async def delete_article(self, blog_id, article_id):
        await self._proxy.delete_article(blog_id, article_id)

    async def get_article_ref_list(self, blog_id, article_id):
        item = await self.get_blog_item(blog_id, article_id)
        return item.ref_list

    async def update_ref(self, blog_id, article_id, ref_id, title, ref):
        await self._proxy.update_ref(blog_id, article_id, ref_id, title, ref)

    async def add_ref(self, blog_id, article_id, title, ref):
        result = await self._proxy.add_ref(blog_id, article_id, title, ref)
        return result.ref_id

    async def delete_ref(self, blog_id, article_id, ref_id):
        await self._proxy.delete_ref(blog_id, article_id, ref_id)

    def invalidate_cache(self):
        self._items_cache.clear()


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self._type_resolver = services.type_resolver
        self._ref_registry = services.ref_registry
        self._async_ref_resolver = services.async_ref_resolver
        self._service_registry = services.service_registry
        self._proxy_factory = services.proxy_factory
        services.blog_service_factory = self._blog_service_factory
        # services.handle_registry.register_type(htypes.blog.blog_article, self._resolve_blog_article)
        # services.handle_registry.register_type(htypes.blog.blog_article_ref_list, self._resolve_blog_article_ref_list)
        services.object_registry.register_type(
            htypes.blog.blog, BlogObject.from_state, services.ref_registry, self._blog_service_factory)
        services.object_registry.register_type(
            htypes.blog.blog_article, BlogArticle.from_state, self._blog_service_factory)
        # services.form_impl_registry.register(
        #     BlogArticleForm.impl_id, BlogArticleForm.from_state, services.ref_registry, self._blog_service_factory, services.handle_resolver)
        # services.objimpl_registry.register(
        #     BlogArticleContents.impl_id, BlogArticleContents.from_state, services.handle_resolver)
        # services.objimpl_registry.register(
        #     ArticleRefListObject.impl_id, ArticleRefListObject.from_state, services.ref_registry, self._blog_service_factory, services.handle_resolver)
        # object_selector.this_module.register_callback(
        #     htypes.blog.selector_callback, SelectorCallback.from_data, services.ref_registry, self._blog_service_factory, services.handle_resolver)

    async def _blog_service_factory(self, blog_service_ref):
        return (await BlogService.from_data(self._type_resolver, self._ref_registry, self._service_registry, self._proxy_factory, blog_service_ref))

    # async def _resolve_blog_article(self, blog_article):
    #     blog_service = await self._blog_service_factory(blog_article.blog_service_ref)
    #     return (await self.open_article(blog_service, blog_article.blog_id, blog_article.article_id))

    # async def open_article(self, blog_service, blog_id, article_id, mode='view'):
    #     item = await blog_service.get_blog_item(blog_id, article_id)
    #     form_object = htypes.blog.blog_article_form(
    #         BlogArticleForm.impl_id, blog_service.to_ref(), blog_id, article_id)
    #     title_object = htypes.line_object.line_object('line', item.title)
    #     contents_object = htypes.blog.blog_article_text(BlogArticleContents.impl_id, item.text, item.ref_list)
    #     return BlogArticleForm.construct(form_object, title_object, contents_object, mode=mode)

    # async def _resolve_blog_article_ref_list(self, ref_list_object):
    #     list_object = htypes.blog.article_ref_list_object(
    #         ArticleRefListObject.impl_id, ref_list_object.blog_service_ref, ref_list_object.blog_id, ref_list_object.article_id)
    #     handle_t = htypes.core.int_list_handle
    #     sort_column_id = 'id'
    #     resource_key = resource_key_t(__module_ref__, ['BlogArticleRefListObject'])
    #     return handle_t('list', list_object, resource_key, key=None)
