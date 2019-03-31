import logging

from hyperapp.common.htypes import resource_key_t
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from . import htypes
from .fs import FsDir
from .tree_object import TreeObject

log = logging.getLogger(__name__)


MODULE_NAME = 'fs_tree'
LOCAL_HOST_NAME = 'local'


class TreeAdapter(TreeObject):

    impl_id = 'fs_dir_tree'

    @classmethod
    async def from_state(cls, state, ref_registry, handle_resolver, fs_service_resolver):
        fs_service = await fs_service_resolver.resolve(state.fs_service_ref)
        dir = FsDir(ref_registry, handle_resolver, fs_service, state.host)
        return cls(dir)

    def __init__(self, dir):
        super().__init__()
        self._dir = dir

    def get_title(self):
        return '%s' % self._dir.host

    def get_state(self):
        return htypes.fs.fs_dir_tree(self.impl_id, self._dir.fs_service_ref, self._dir.host, [], current_name=None)

    def get_columns(self):
        return self._dir.get_columns()

    async def fetch_items(self, path):
        from_key = None
        while True:
            result = await self._dir.fetch_items(path, from_key)
            self._distribute_fetch_results(path, result.item_list)
            for item in result.item_list:
                if item.ftype != 'dir':
                    # signal there are no children
                    self._distribute_fetch_results(list(path) + [item.key], [])
            if result.eof:
                self._distribute_eof()
                break
            from_key = result.item_list[-1].key


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        self._local_fs_service_ref = services.local_fs_service_ref
        services.objimpl_registry.register(
            TreeAdapter.impl_id, TreeAdapter.from_state, services.ref_registry, services.handle_resolver, services.fs_service_resolver)

    @command('open_local_fs_tree')
    async def open_local_fs_tree(self):
        fs_service_ref = self._local_fs_service_ref
        path = 'usr/share/doc'.split('/')
        dir_tree = htypes.fs.fs_dir_tree(TreeAdapter.impl_id, fs_service_ref, LOCAL_HOST_NAME, path, current_name=None)
        resource_key = resource_key_t(__module_ref__, ['fs-tree'])
        return htypes.tree_view.tree_handle('tree', dir_tree, resource_key)
