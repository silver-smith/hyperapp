import logging
import asyncio
import uuid
import abc

from ..common.htypes import tInt, tDateTime
from ..common.interface import core as core_types
from ..common.interface import hyper_ref as href_types
from ..common.interface import blog as blog_types
from ..common.interface import line_object as line_object_types
from ..common.interface import text_object as text_object_types
from ..common.interface import form as form_types
from ..common.interface import object_selector as object_selector_types
from ..common.list_object import Element, Chunk, ListDiff
from .module import ClientModule
from .command import command
from .mode_command import mode_command
from .text_object import TextObject
from .list_object import Column, ListObject
from .form import FormObject, FormView
from . import object_selector

log = logging.getLogger(__name__)


MODULE_NAME = 'blog'


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

    impl_id = 'blog'

    @classmethod
    async def from_state(cls, state, ref_registry, blog_service_factory, handle_resolver):
        blog_service = await blog_service_factory(state.blog_service_ref)
        return cls(ref_registry, handle_resolver, blog_service, state.blog_id)

    def __init__(self, ref_registry, handle_resolver, blog_service, blog_id):
        ListObject.__init__(self)
        self._ref_registry = ref_registry
        self._handle_resolver = handle_resolver
        self._blog_service = blog_service
        self._blog_id = blog_id
        log.debug('Created %r', self)

    def __repr__(self):
        return '<BlogObject#%d>' % id(self)

    def __del__(self):
        log.debug('Deleted %r', self)

    def get_state(self):
        return blog_types.blog_object(self.impl_id, self._blog_service.to_ref(), self._blog_id)

    def get_title(self):
        return self._blog_id

    def pick_current_refs(self):
        return []

    def observers_arrived(self):
        asyncio.async(self._blog_service.add_observer(self._blog_id, self))

    def observers_gone(self):
        self._blog_service.remove_observer(self._blog_id, self)

    def get_columns(self):
        return [
            Column('id', type=tInt, is_key=True),
            Column('created_at', type=tDateTime),
            Column('title'),
            ]

    def get_key_column_id(self):
        return 'id'

    async def fetch_elements_impl(self, sort_column_id, from_key, desc_count, asc_count):
        chunk = await self._blog_service.fetch_blog_contents(
            self._blog_id, sort_column_id, from_key, desc_count, asc_count)
        elements = [self._row_to_element(row, sort_column_id) for row in chunk.rows]
        return Chunk(sort_column_id, from_key, elements, chunk.bof, chunk.eof)

    def _row_to_element(self, row, sort_column_id=None):
        if sort_column_id:
            order_key = getattr(row, sort_column_id)
        else:
            # order_key is not used for diffs - every view has it's own
            order_key = None
        return Element(row.id, row, commands=None, order_key=order_key)

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
    async def command_open(self, element_key):
        return (await self._open_article(article_id=element_key))

    @command('delete', kind='element')
    async def command_delete(self, element_key):
        await self._blog_service.delete_article(self._blog_id, article_id=element_key)

    @command('add')
    async def command_add(self):
        article_id = await self._blog_service.create_article(self._blog_id, 'Untitled', '')
        return (await self._open_article(article_id))

    async def _open_article(self, article_id):
        blog_service_ref = self._blog_service.to_ref()
        object = blog_types.blog_article_ref(blog_service_ref, self._blog_id, article_id)
        ref = self._ref_registry.register_object(object)
        return (await self._handle_resolver.resolve(ref))


class BlogArticleForm(FormObject):

    impl_id = 'blog_article_form'

    @classmethod
    async def from_state(cls, state, field_object_map, ref_registry, blog_service_factory, handle_resolver):
        blog_service = await blog_service_factory(state.blog_service_ref)
        return cls(field_object_map, ref_registry, handle_resolver, blog_service, state.blog_id, state.article_id)

    @classmethod
    def construct(cls, form_object, title_object, contents_object, mode, current_field_id=None):
        title_view = line_object_types.line_edit_view('line_edit', title_object, mode=mode)
        if mode == 'view':
            contents_view = core_types.obj_handle('text_view', contents_object)
        else:
            contents_view = core_types.obj_handle('text_edit', contents_object)
        form_view = form_types.form_handle('form', form_object, [
            form_types.form_view_field('title', title_view),
            form_types.form_view_field('text', contents_view),
            ], mode=mode, current_field_id=current_field_id or 'text')
        return form_view

    def __init__(self, field_object_map, ref_registry, handle_resolver, blog_service, blog_id, article_id):
        super().__init__(field_object_map)
        self._ref_registry = ref_registry
        self._handle_resolver = handle_resolver
        self._blog_service = blog_service
        self._blog_id = blog_id
        self._article_id = article_id

    def get_title(self):
        return self._fields['title'].line

    def get_state(self):
        return blog_types.blog_article_form(self.impl_id, self._blog_service.to_ref(), self._blog_id, self._article_id)

    @mode_command('edit', mode=FormView.Mode.VIEW)
    def command_edit(self):
        return self._open_in_mode('edit')

    @mode_command('view', mode=FormView.Mode.EDIT)
    def command_view(self):
        return self._open_in_mode('view')

    def _open_in_mode(self, mode):
        return self.construct(
            form_object=self.get_state(),
            title_object=self._fields['title'].get_state(),
            contents_object=self._fields['text'].get_state(),
            mode=mode,
            )

    @command('refs')
    async def command_refs(self):
        blog_service_ref = self._blog_service.to_ref()
        object = blog_types.blog_article_ref_list_ref(blog_service_ref, self._blog_id, self._article_id)
        ref = self._ref_registry.register_object(object)
        return (await self._handle_resolver.resolve(ref))

    @mode_command('save', mode=FormView.Mode.EDIT)
    async def command_save(self):
        title = self._fields['title'].line
        text = self._fields['text'].text
        await self._blog_service.save_article(self._blog_id, self._article_id, title, text)


class BlogArticleContents(TextObject):

    impl_id = 'blog_article_contents'

    @classmethod
    def from_state(cls, state, handle_resolver):
        return cls(handle_resolver, state.text, state.ref_list)

    def __init__(self, handle_resolver, text, ref_list):
        super().__init__(text)
        self._handle_resolver = handle_resolver
        self._ref_list = ref_list

    def get_title(self):
        return None

    def get_state(self):
        return blog_types.blog_article_text(self.impl_id, self._text, self._ref_list)

    async def open_ref(self, id):
        log.info('Opening ref: %r', id)
        id2ref = {ref.id: ref.ref for ref in self._ref_list}
        ref = id2ref.get(int(id))
        if not ref:
            log.warning('ref is missing: %r', id)
            return
        return (await self._handle_resolver.resolve(ref))


class ArticleRefListObject(ListObject):

    impl_id = 'article-ref-list'

    @classmethod
    async def from_state(cls, state, ref_registry, blog_service_factory, handle_resolver):
        blog_service = await blog_service_factory(state.blog_service_ref)
        return cls(ref_registry, handle_resolver, blog_service, state.blog_id, state.article_id)

    def __init__(self, ref_registry, handle_resolver, blog_service, blog_id, article_id):
        ListObject.__init__(self)
        self._ref_registry = ref_registry
        self._handle_resolver = handle_resolver
        self._blog_service = blog_service
        self._blog_id = blog_id
        self._article_id = article_id
        self._id2ref = {}

    def get_state(self):
        return blog_types.article_ref_list_object(self.impl_id, self._blog_service.to_ref(), self._blog_id, self._article_id)

    def get_title(self):
        return 'refs for %s:%d' % (self._blog_id, self._article_id)

    def pick_current_refs(self):
        return []

    def get_columns(self):
        return [
            Column('id', type=tInt, is_key=True),
            Column('title'),
            Column('ref'),
            ]

    def get_key_column_id(self):
        return 'id'

    async def fetch_elements_impl(self, sort_column_id, from_key, desc_count, asc_count):
        ref_list = await self._blog_service.get_article_ref_list(self._blog_id, self._article_id)
        self._id2ref.update({row.id: row.ref for row in ref_list})
        elements = [Element(row.id, row, commands=None, order_key=getattr(row, sort_column_id))
                    for row in ref_list]
        return Chunk(sort_column_id, from_key=None, elements=elements, bof=True, eof=True)

    async def get_ref_handle(self, id):
        ref = self._id2ref[id]
        return (await self._handle_resolver.resolve(ref))

    @command('open', kind='element')
    async def command_open(self, element_key):
        return (await self.get_ref_handle(element_key))

    @command('add')
    async def command_add(self):
        blog_service_ref = self._blog_service.to_ref()
        article_ref_list_object = blog_types.blog_article_ref_list_ref(blog_service_ref, self._blog_id, self._article_id)
        target_ref = self._ref_registry.register_object(article_ref_list_object)
        target_handle = await self._handle_resolver.resolve(target_ref)
        callback = blog_types.selector_callback(self._blog_service.to_ref(), self._blog_id, self._article_id)
        object = object_selector_types.object_selector_object('object_selector', callback)
        return object_selector_types.object_selector_view('object_selector', object, target_handle)

    @command('change', kind='element')
    async def command_change(self, element_key):
        target_handle = await self.get_ref_handle(element_key)
        callback = blog_types.selector_callback(self._blog_service.to_ref(), self._blog_id, self._article_id, element_key)
        object = object_selector_types.object_selector_object('object_selector', callback)
        return object_selector_types.object_selector_view('object_selector', object, target_handle)

    @command('delete', kind='element')
    async def command_delete(self, element_key):
        await self._blog_service.delete_ref(self._blog_id, self._article_id, element_key)


class SelectorCallback(object):

    @classmethod
    async def from_data(cls, state, ref_registry, blog_service_factory, handle_resolver):
        blog_service = await blog_service_factory(state.blog_service_ref)
        return cls(ref_registry, handle_resolver, blog_service, state.blog_id, state.article_id, state.ref_id)

    def __init__(self, ref_registry, handle_resolver, blog_service, blog_id, article_id, ref_id):
        self._ref_registry = ref_registry
        self._handle_resolver = handle_resolver
        self._blog_service = blog_service
        self._blog_id = blog_id
        self._article_id = article_id
        self._ref_id = ref_id

    async def set_ref(self, title, ref):
        if self._ref_id is not None:
            await self._blog_service.update_ref(self._blog_id, self._article_id, self._ref_id, title, ref)
            ref_id = self._ref_id
        else:
            ref_id = await self._blog_service.add_ref(self._blog_id, self._article_id, title, ref)
        blog_service_ref = self._blog_service.to_ref()
        object = blog_types.blog_article_ref_list_ref(blog_service_ref, self._blog_id, self._article_id, ref_id)
        ref = self._ref_registry.register_object(object)
        return (await self._handle_resolver.resolve(ref))

    def to_data(self):
        return blog_types.selector_callback(self._blog_service.to_ref(), self._blog_id, self._article_id, self._ref_id)
    

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
    async def from_data(cls, ref_registry, service_registry, proxy_factory, service_ref):
        proxy = await proxy_factory.from_ref(service_ref)
        return cls(ref_registry, service_registry, proxy)

    def __init__(self, ref_registry, service_registry, proxy):
        self._ref_registry = ref_registry
        self._service_registry = service_registry
        self._proxy = proxy
        self._rows_cache = {}  # (blog_id, article_id) -> blog_row, already fetched rows
        self._blog_id_to_observer_set = {}
        self._subscribed_to_blog_id_set = set()
        self._notification = BlogNotification(self)

    def to_ref(self):
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
        service = href_types.service(service_id, ['blog', 'blog_notification_iface'])
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

    async def fetch_blog_contents(self, blog_id, sort_column_id, from_key, desc_count, asc_count):
        fetch_request = blog_types.row_fetch_request(sort_column_id, from_key, desc_count, asc_count)
        result = await self._proxy.fetch_blog_contents(blog_id, fetch_request)
        self._rows_cache.update({(blog_id, row.id): row for row in result.chunk.rows})
        return result.chunk

    async def get_blog_row(self, blog_id, article_id):
        row = self._rows_cache.get((blog_id, article_id))
        if not row:
            await self.fetch_blog_contents(blog_id, sort_column_id='id', from_key=article_id, desc_count=1, asc_count=0)
            row = self._rows_cache.get((blog_id, article_id))
            assert row, repr((blog_id, article_id))  # expecting it to be fetched now
        return row

    async def create_article(self, blog_id, title, text):
        result = await self._proxy.create_article(blog_id, title, text)
        row = result.blog_row
        self._rows_cache[(blog_id, row.id)] = row
        return row.id

    async def save_article(self, blog_id, article_id, title, text):
        await self._proxy.save_article(blog_id, article_id, title, text)

    async def delete_article(self, blog_id, article_id):
        await self._proxy.delete_article(blog_id, article_id)

    async def get_article_ref_list(self, blog_id, article_id):
        row = await self.get_blog_row(blog_id, article_id)
        return row.ref_list

    async def update_ref(self, blog_id, article_id, ref_id, title, ref):
        await self._proxy.update_ref(blog_id, article_id, ref_id, title, ref)

    async def add_ref(self, blog_id, article_id, title, ref):
        result = await self._proxy.add_ref(blog_id, article_id, title, ref)
        return result.ref_id

    async def delete_ref(self, blog_id, article_id, ref_id):
        await self._proxy.delete_ref(blog_id, article_id, ref_id)

    def invalidate_cache(self):
        self._rows_cache.clear()


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        self._ref_registry = services.ref_registry
        self._async_ref_resolver = services.async_ref_resolver
        self._service_registry = services.service_registry
        self._proxy_factory = services.proxy_factory
        services.blog_service_factory = self._blog_service_factory
        services.handle_registry.register(blog_types.blog_ref, self._resolve_blog_object)
        services.handle_registry.register(blog_types.blog_article_ref, self._resolve_blog_article_object)
        services.handle_registry.register(blog_types.blog_article_ref_list_ref, self._resolve_blog_article_ref_list_object)
        services.objimpl_registry.register(
            BlogObject.impl_id, BlogObject.from_state, services.ref_registry, self._blog_service_factory, services.handle_resolver)
        services.form_impl_registry.register(
            BlogArticleForm.impl_id, BlogArticleForm.from_state, services.ref_registry, self._blog_service_factory, services.handle_resolver)
        services.objimpl_registry.register(
            BlogArticleContents.impl_id, BlogArticleContents.from_state, services.handle_resolver)
        services.objimpl_registry.register(
            ArticleRefListObject.impl_id, ArticleRefListObject.from_state, services.ref_registry, self._blog_service_factory, services.handle_resolver)
        object_selector.this_module.register_callback(
            blog_types.selector_callback, SelectorCallback.from_data, services.ref_registry, self._blog_service_factory, services.handle_resolver)

    async def _blog_service_factory(self, blog_service_ref):
        return (await BlogService.from_data(self._ref_registry, self._service_registry, self._proxy_factory, blog_service_ref))

    async def _resolve_blog_object(self, blog_object_ref, blog_object):
        list_object = blog_types.blog_object(BlogObject.impl_id, blog_object.blog_service_ref, blog_object.blog_id)
        handle_t = core_types.int_list_handle
        sort_column_id = 'created_at'
        resource_id = ['client_module', 'blog', 'BlogObject']
        return handle_t('list', list_object, resource_id, sort_column_id, key=None)

    async def _resolve_blog_article_object(self, blog_article_object_ref, blog_article_object):
        blog_service = await self._blog_service_factory(blog_article_object.blog_service_ref)
        row = await blog_service.get_blog_row(blog_article_object.blog_id, blog_article_object.article_id)
        form_object = blog_types.blog_article_form(
            BlogArticleForm.impl_id, blog_article_object.blog_service_ref, blog_article_object.blog_id, blog_article_object.article_id)
        title_object = line_object_types.line_object('line', row.title)
        contents_object = blog_types.blog_article_text(BlogArticleContents.impl_id, row.text, row.ref_list)
        return BlogArticleForm.construct(form_object, title_object, contents_object, mode='view')

    async def _resolve_blog_article_ref_list_object(self, ref_list_object_ref, ref_list_object):
        list_object = blog_types.article_ref_list_object(
            ArticleRefListObject.impl_id, ref_list_object.blog_service_ref, ref_list_object.blog_id, ref_list_object.article_id)
        handle_t = core_types.int_list_handle
        sort_column_id = 'id'
        resource_id = ['client_module', 'blog', 'BlogArticleRefListObject']
        return handle_t('list', list_object, resource_id, sort_column_id, key=None)
