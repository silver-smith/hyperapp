import asyncio
import logging

from ..common.htypes import tInt, tString, Column, list_handle_type
from ..common.url import Url
from ..common.interface import core as core_types
from ..common.interface import blog as blog_types
from .module import Module
from .list_object import ListObject

log = logging.getLogger(__name__)


class BlogObject(ListObject):

    objimpl_id = 'blog'

    @classmethod
    def from_state(cls, state, href_registry, href_resolver, service_registry):
        blog_service = service_registry.resolve(state.blog_service)
        return cls(href_registry, href_resolver, blog_service, state.blog_id)

    def __init__(self, href_registry, href_resolver, blog_service, blog_id):
        ListObject.__init__(self)
        self._href_registry = href_registry
        self._href_resolver = href_resolver
        self._blog_service = blog_service
        self._blog_id = blog_id
        self._key2row = {}  # cache for visited rows

    def get_state(self):
        return blog_types.blog_object(self.objimpl_id, self._blog_service.to_data(), self._blog_id)

    def get_title(self):
        return self._blog_id

    def pick_current_refs(self):
        return []

    def get_columns(self):
        return [
            Column('id', type=tInt, is_key=True),
            Column('title'),
            ]

    def get_key_column_id(self):
        return 'id'

    @asyncio.coroutine
    def fetch_elements(self, sort_column_id, from_key, desc_count, asc_count):
        chunk = yield from self._blog_service.fetch_blog_contents(
            self._blog_id, sort_column_id, from_key, desc_count, asc_count)
        self._key2row.update({row.id: row for row in chunk.rows})
        elements = [Element(row.key, row, commands=None, order_key=getattr(row, sort_column_id))
                    for row in chunk.rows]
        list_chunk = Chunk(sort_column_id, from_key, elements, chunk.bof, chunk.eof)
        self._notify_fetch_result(list_chunk)
        return list_chunk

    def process_diff(self, diff):
        assert isinstance(diff, ListDiff), repr(diff)
        log.info('-- BlogDirObject.process_diff self=%r diff=%r', id(self), diff)


class BlogService(object):

    @classmethod
    def from_data(cls, service_object, iface_registry, proxy_factory):
        service_url = Url.from_data(iface_registry, service_object.service_url)
        service_proxy = proxy_factory.from_url(service_url)
        return cls(service_proxy)

    def __init__(self, service_proxy):
        self._service_proxy = service_proxy

    def to_data(self):
        service_url = self._service_proxy.get_url()
        return blog_types.blog_service(service_url.to_data())

    def to_service_ref(self):
        return href_types.service_ref('sha256', b'test-blog-service-ref')

    @asyncio.coroutine
    def fetch_blog_contents(self, blog_id, sort_column_id, from_key, desc_count, asc_count):
        fetch_request = blog_types.row_fetch_request(sort_column_id, from_key, desc_count, asc_count)
        result = yield from self._service_proxy.fetch_blog_contents(blog_id, fetch_request)
        return result.chunk


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._href_resolver = services.href_resolver
        self._service_registry = services.service_registry
        services.href_object_registry.register(blog_types.blog_ref.id, self.resolve_blog_object)
        services.service_registry.register(
            blog_types.blog_service.id, BlogService.from_data, services.iface_registry, services.proxy_factory)
        services.objimpl_registry.register(
            BlogObject.objimpl_id, BlogObject.from_state, services.href_registry, services.href_resolver, services.service_registry)

    @asyncio.coroutine
    def resolve_blog_object(self, blog_object):
        blog_service_object = yield from self._href_resolver.resolve_service_ref(blog_object.blog_service_ref)
        dir_object = blog_types.blog_object(BlogObject.objimpl_id, blog_service_object, blog_object.blog_id)
        handle_t = list_handle_type(core_types, tInt)
        sort_column_id = 'id'
        resource_id = ['client_module', 'blog', 'BlogObject']
        return handle_t('list', dir_object, resource_id, sort_column_id, None)
