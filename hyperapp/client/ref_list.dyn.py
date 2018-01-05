import logging
import codecs
from operator import attrgetter
from collections import namedtuple

from ..common.htypes import tInt, tString, Column, list_handle_type
from ..common.interface import core as core_types
from ..common.interface import ref_list as ref_list_types
from ..common.url import Url
from ..common.list_object import Element, Chunk
from .command import command
from .module import Module
from .list_object import ListObject

log = logging.getLogger(__name__)


class RefListObject(ListObject):

    objimpl_id = 'ref_list'

    Row = namedtuple('RefListObject_Row', 'id ref')

    @classmethod
    def from_state(cls, state, ref_resolver, iface_registry, proxy_factory):
        ref_list_service = RefListService.from_data(state.ref_list_service, iface_registry, proxy_factory)
        return cls(ref_resolver, ref_list_service, state.ref_list_id)

    def __init__(self, ref_resolver, ref_list_service, ref_list_id):
        ListObject.__init__(self)
        self._ref_resolver = ref_resolver
        self._ref_list_service = ref_list_service
        self._ref_list_id = ref_list_id
        self._id2ref = None
        self._rows = None

    def get_state(self):
        return ref_list_types.ref_list_object(self.objimpl_id, self._ref_list_service.to_data(), self._ref_list_id)

    def get_title(self):
        return 'Ref List %s' % self._ref_list_id

    def get_columns(self):
        return [
            Column('id', is_key=True),
            Column('ref'),
            ]

    def get_key_column_id(self):
        return 'id'

    async def fetch_elements(self, sort_column_id, from_key, desc_count, asc_count):
        if not self._rows:
            ref_list = await self._ref_list_service.get_ref_list(self._ref_list_id)
            assert sort_column_id in ['id', 'ref'], repr(sort_column_id)
            self._rows = [self.Row(ref_item.id, codecs.encode(ref_item.ref, 'hex'))
                          for ref_item in ref_list.ref_list]
            self._id2ref = {ref_item.id: ref_item.ref for ref_item in ref_list.ref_list}
        sorted_rows = sorted(self._rows, key=attrgetter(sort_column_id))
        elements = [Element(row.id, row, commands=None, order_key=getattr(row, sort_column_id)) for row in sorted_rows]
        chunk = Chunk(sort_column_id, None, elements, True, True)
        self._notify_fetch_result(chunk)
        return chunk

    @command('open', kind='element')
    async def command_open(self, element_key):
        assert self._id2ref is not None  # fetch_element was not called yet
        ref = self._id2ref[element_key]
        log.info('Opening ref %r: %r', element_key, ref)
        return (await self._ref_resolver.resolve_ref_to_handle(ref))

    def process_diff(self, diff):
        assert isinstance(diff, ListDiff), repr(diff)
        log.info('-- FsDirObject.process_diff self=%r diff=%r', id(self), diff)


class RefListService(object):

    @classmethod
    def from_data(cls, service_object, iface_registry, proxy_factory):
        return cls.from_url(service_object.service_url, iface_registry, proxy_factory)

    @classmethod
    def from_url(cls, url, iface_registry, proxy_factory):
        service_url = Url.from_data(iface_registry, url)
        service_proxy = proxy_factory.from_url(service_url)
        return cls(service_proxy)

    def __init__(self, service_proxy):
        self._service_proxy = service_proxy

    def to_data(self):
        service_url = self._service_proxy.get_url()
        return ref_list_types.ref_list_service(service_url.to_data())

    async def get_ref_list(self, ref_list_id):
        result = await self._service_proxy.get_ref_list(ref_list_id)
        return result.ref_list


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._ref_resolver = services.ref_resolver
        services.referred_registry.register(ref_list_types.dynamic_ref_list, self.resolve_dynamic_ref_list_object)
        services.objimpl_registry.register(
            RefListObject.objimpl_id, RefListObject.from_state, services.ref_resolver, services.iface_registry, services.proxy_factory)

    async def resolve_dynamic_ref_list_object(self, dynamic_ref_list):
        ref_list_service = await self._ref_resolver.resolve_ref_to_object(dynamic_ref_list.ref_list_service)
        object = ref_list_types.ref_list_object(RefListObject.objimpl_id, ref_list_service, dynamic_ref_list.ref_list_id)
        handle_t = list_handle_type(core_types, tString)
        sort_column_id = 'id'
        resource_id = ['client_module', 'ref_list', 'RefListObject']
        return handle_t('list', object, resource_id, sort_column_id, None)
