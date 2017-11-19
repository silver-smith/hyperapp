from operator import attrgetter
from collections import namedtuple
import asyncio
from ..common.htypes import tInt, tString, Column, list_handle_type
from ..common.interface import core as core_types
from ..common.interface import href_list as href_list_types
from ..common.url import Url
from ..common.list_object import Element, Chunk
from .command import command
from .module import Module
from .list_object import ListObject


class HRefListObject(ListObject):

    objimpl_id = 'href_list'

    Row = namedtuple('HRefListObject_Row', 'id href')

    @classmethod
    def from_state(cls, state, service_registry):
        href_list_service = service_registry.resolve(state.href_list_service)
        return cls(href_list_service, state.href_list_id)

    def __init__(self, href_list_service, href_list_id):
        ListObject.__init__(self)
        self._href_list_service = href_list_service
        self._href_list_id = href_list_id

    def get_state(self):
        return href_list_types.href_list_object(self.objimpl_id, self._href_list_service.to_data(), self._href_list_id)

    def get_title(self):
        return 'HRef List %s' % self._href_list_id

    def get_columns(self):
        return [
            Column('id', is_key=True),
            Column('href'),
            ]

    def get_key_column_id(self):
        return 'id'

    @asyncio.coroutine
    def fetch_elements(self, sort_column_id, from_key, desc_count, asc_count):
        href_list = yield from self._href_list_service.get_href_list(self._href_list_id)
        assert sort_column_id in ['id', 'href'], repr(sort_column_id)
        rows = [self.Row(href_item.id, '%s.%s' % (href_item.href.algorithm, href_item.href.hash.decode()))
                for href_item in href_list.href_list]
        sorted_rows = sorted(rows, key=attrgetter(sort_column_id))
        elements = [Element(row.id, row, commands=None, order_key=getattr(row, sort_column_id)) for row in sorted_rows]
        chunk = Chunk(sort_column_id, None, elements, True, True)
        self._notify_fetch_result(chunk)
        return chunk

    @command('open', kind='element')
    def command_open(self, element_key):
        assert False, repr(element_key)

    def process_diff(self, diff):
        assert isinstance(diff, ListDiff), repr(diff)
        log.info('-- FsDirObject.process_diff self=%r diff=%r', id(self), diff)


class HRefListService(object):

    @classmethod
    def from_data(cls, service_object, iface_registry, proxy_factory):
        service_url = Url.from_data(iface_registry, service_object.service_url)
        service_proxy = proxy_factory.from_url(service_url)
        return cls(service_proxy)

    def __init__(self, service_proxy):
        self._service_proxy = service_proxy

    def to_data(self):
        service_url = self._service_proxy.get_url()
        return href_list_types.href_list_service(service_url.to_data())

    @asyncio.coroutine
    def get_href_list(self, href_list_id):
        result = yield from self._service_proxy.get_href_list(href_list_id)
        return result.href_list


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._href_resolver = services.href_resolver
        self._service_registry = services.service_registry
        services.href_object_registry.register(href_list_types.dynamic_href_list.id, self.resolve_dynamic_href_list_object)
        services.service_registry.register(href_list_types.href_list_service.id, HRefListService.from_data, services.iface_registry, services.proxy_factory)
        services.objimpl_registry.register(HRefListObject.objimpl_id, HRefListObject.from_state, services.service_registry)

    @asyncio.coroutine
    def resolve_dynamic_href_list_object(self, dynamic_href_list):
        href_list_service = yield from self._href_resolver.resolve_service_ref(dynamic_href_list.href_list_service)
        object = href_list_types.href_list_object(HRefListObject.objimpl_id, href_list_service, dynamic_href_list.href_list_id)
        handle_t = list_handle_type(core_types, tString)
        sort_column_id = 'id'
        resource_id = ['client', 'href_list']
        return handle_t('list', object, resource_id, sort_column_id, None)
