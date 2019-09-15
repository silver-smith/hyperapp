from collections import namedtuple
import logging

from hyperapp.common.htypes import tInt, tString, resource_key_t
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from .async_capsule_registry import AsyncCapsuleRegistry, AsyncCapsuleResolver
from . import htypes
from .column import Column
from .tree_object import TreeObject

log = logging.getLogger(__name__)


FetchResult = namedtuple('FetchResult', 'item_list eof')


class FsTree(TreeObject):

    @classmethod
    async def from_state(cls, state, fs_service_resolver):
        fs_service = await fs_service_resolver.resolve(state.fs_service_ref)
        return cls(fs_service, state.host)

    def __init__(self, fs_service, host):
        super().__init__()
        self._fs_service = fs_service
        self._host = host

    def get_title(self):
        return '%s' % self._host

    def get_columns(self):
        return [
            Column('key', is_key=True),
            Column('ftype'),
            Column('ftime', type=tInt),
            Column('fsize', type=tInt),
            ]

    async def fetch_items(self, path):
        from_key = None
        while True:
            result = await self._fetch_items(path, from_key)
            self._distribute_fetch_results(path, result.item_list)
            for item in result.item_list:
                if item.ftype != 'dir':
                    # signal there are no children
                    self._distribute_fetch_results(list(path) + [item.key], [])
            if result.eof:
                break
            from_key = result.item_list[-1].key

    async def _fetch_items(self, path, from_key=None):
        chunk = await self._fs_service.fetch_dir_contents(
            self._host, list(path),
            sort_column_id='key',
            from_key=from_key,
            desc_count=0,
            asc_count=50,
            )
        return FetchResult(
            item_list=chunk.rows,
            eof=chunk.eof,
            )


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.fs_service_registry = fs_service_registry = AsyncCapsuleRegistry('fs_service', services.type_resolver)
        services.fs_service_resolver = fs_service_resolver = AsyncCapsuleResolver(services.async_ref_resolver, fs_service_registry)
        services.object_registry.register_type(
            htypes.fs.fs, FsTree.from_state, services.fs_service_resolver)
