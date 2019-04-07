import logging
from operator import attrgetter
from collections import namedtuple

from hyperapp.common.htypes import resource_key_t
from hyperapp.common.ref import ref_repr
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from . import htypes
from .list_object import Column, ListObject

log = logging.getLogger(__name__)


MODULE_NAME = 'ref_list'


class RefListObject(ListObject):

    impl_id = 'ref_list'

    _Item = namedtuple('RefListObject_Item', 'id ref')

    @classmethod
    async def from_state(cls, state, handle_resolver, proxy_factory):
        ref_list_service = await RefListService.from_ref(state.ref_list_service, proxy_factory)
        return cls(handle_resolver, ref_list_service, state.ref_list_id)

    def __init__(self, handle_resolver, ref_list_service, ref_list_id):
        ListObject.__init__(self)
        self._handle_resolver = handle_resolver
        self._ref_list_service = ref_list_service
        self._ref_list_id = ref_list_id
        self._id2ref = None
        self._item_list = None

    def get_state(self):
        return htypes.ref_list.ref_list_object(self.impl_id, self._ref_list_service.to_ref(), self._ref_list_id)

    def get_title(self):
        return 'Ref List %s' % self._ref_list_id

    def get_columns(self):
        return [
            Column('id', is_key=True),
            Column('ref'),
            ]

    async def fetch_items(self, from_key):
        if self._item_list is None:
            ref_list = await self._ref_list_service.get_ref_list(self._ref_list_id)
            self._item_list = [self._Item(ref_item.id, ref_repr(ref_item.ref))
                               for ref_item in ref_list.ref_list]
            self._id2ref = {ref_item.id: ref_item.ref for ref_item in ref_list.ref_list}
        self._distribute_fetch_results(self._item_list)
        self._distribute_eof()

    @command('open', kind='element')
    async def command_open(self, item_id):
        assert self._id2ref is not None  # fetch_element was not called yet
        ref = self._id2ref[item_id]
        log.info('Opening ref %r: %s', item_id, ref_repr(ref))
        return (await self._handle_resolver.resolve(ref))


class RefListService(object):

    @classmethod
    async def from_ref(cls, service_ref, proxy_factory):
        proxy = await proxy_factory.from_ref(service_ref)
        return cls(proxy)

    def __init__(self, proxy):
        self._proxy = proxy

    def to_ref(self):
        return self._proxy.service_ref

    async def get_ref_list(self, ref_list_id):
        result = await self._proxy.get_ref_list(ref_list_id)
        return result.ref_list


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.handle_registry.register_type(htypes.ref_list.dynamic_ref_list, self._resolve_dynamic_ref_list_object)
        services.objimpl_registry.register(
            RefListObject.impl_id, RefListObject.from_state, services.handle_resolver, services.proxy_factory)

    async def _resolve_dynamic_ref_list_object(self, dynamic_ref_list_ref, dynamic_ref_list):
        object = htypes.ref_list.ref_list_object(RefListObject.impl_id, dynamic_ref_list.ref_list_service, dynamic_ref_list.ref_list_id)
        handle_t = htypes.core.string_list_handle
        sort_column_id = 'id'
        resource_key = resource_key_t(__module_ref__, ['RefListObject'])
        return handle_t('list', object, resource_key, None)
