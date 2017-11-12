import asyncio
from ..common.htypes import tInt, tString, Column, list_handle_type
from ..common.interface import core as core_types
from ..common.interface import ref_list as ref_list_types
from ..common.url import Url
from .module import Module
from .list_object import ListObject


class RefListObject(ListObject):

    objimpl_id = 'ref_list'

    @classmethod
    def from_state(cls, state, service_registry):
        ref_list_service = service_registry.resolve(state.ref_list_service)
        return cls(ref_list_service, state.ref_list_id)

    def __init__(self, ref_list_service, ref_list_id):
        ListObject.__init__(self)
        self._ref_list_service = ref_list_service
        self._ref_list_id = ref_list_id

    def get_state(self):
        return ref_list_types.ref_list_object(self.objimpl_id, self._ref_list_service.to_data(), self._ref_list_id)

    def get_title(self):
        return 'Ref List %s' % self._ref_list_id

    def get_commands(self):
        return ListObject.get_commands(self)

    def get_columns(self):
        return [
            Column('id', is_key=True),
            ]

    def get_key_column_id(self):
        return 'id'

    @asyncio.coroutine
    def fetch_elements(self, sort_column_id, from_key, desc_count, asc_count):
        chunk = yield from self._ref_list_service.fetch_dir_contents(
            self._host, self._path, sort_column_id, from_key, desc_count, asc_count)
        elements = [Element(row.key, row, commands=None, order_key=getattr(row, sort_column_id))
                    for row in chunk.rows]
        list_chunk = Chunk(sort_column_id, from_key, elements, chunk.bof, chunk.eof)
        self._notify_fetch_result(list_chunk)
        return list_chunk

    def process_diff(self, diff):
        assert isinstance(diff, ListDiff), repr(diff)
        log.info('-- FsDirObject.process_diff self=%r diff=%r', id(self), diff)


class RefListService(object):

    @classmethod
    def from_data(cls, service_object, iface_registry, proxy_factory):
        service_url = Url.from_data(iface_registry, service_object.service_url)
        service_proxy = proxy_factory.from_url(service_url)
        return cls(service_proxy)

    def __init__(self, service_proxy):
        self._service_proxy = service_proxy

    def to_data(self):
        service_url = self._service_proxy.get_url()
        return ref_list_types.ref_list_service(service_url.to_data())

    @asyncio.coroutine
    def get_ref_list(self, ref_list_id):
        result = yield from self._service_proxy.get_ref_list(ref_list_id)
        return result.chunk


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._href_resolver = services.href_resolver
        self._service_registry = services.service_registry
        services.href_object_registry.register(ref_list_types.dynamic_ref_list.id, self.resolve_dynamic_ref_list_object)
        services.service_registry.register(ref_list_types.ref_list_service.id, RefListService.from_data, services.iface_registry, services.proxy_factory)
        services.objimpl_registry.register(RefListObject.objimpl_id, RefListObject.from_state, services.service_registry)

    @asyncio.coroutine
    def resolve_dynamic_ref_list_object(self, dynamic_ref_list):
        ref_list_service = yield from self._href_resolver.resolve_service_ref(dynamic_ref_list.ref_list_service)
        object = ref_list_types.ref_list_object(RefListObject.objimpl_id, ref_list_service, dynamic_ref_list.ref_list_id)
        handle_t = list_handle_type(core_types, tString)
        sort_column_id = 'id'
        resource_id = ['client', 'ref_list']
        return handle_t('list', object, resource_id, sort_column_id, None)
