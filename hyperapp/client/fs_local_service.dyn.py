import logging
import os.path

from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from .fs_service_impl import FsServiceImpl
from . import htypes

log = logging.getLogger(__name__)


MODULE_NAME = 'fs.local'
LOCAL_HOST_NAME = 'local'


class LocalFsService(object):

    @classmethod
    def from_data(cls, unused_local_fs_service_ref, unused_local_fs_service, ref_registry):
        return cls(ref_registry)

    def __init__(self, ref_registry):
        self._ref_registry = ref_registry
        self._impl = FsServiceImpl()

    def to_ref(self):
        local_fs_service = htypes.fs.local_fs_service()
        return self._ref_registry.register_object(local_fs_service)

    async def fetch_dir_contents(self, host, path, sort_column_id, from_key, desc_count, asc_count):
        assert host == LOCAL_HOST_NAME, repr(host)
        fetch_request = htypes.fs.row_fetch_request(sort_column_id, from_key, desc_count, asc_count)
        return self._impl.fetch_dir_contents(path, fetch_request)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        ref_registry = services.ref_registry
        self._handle_resolver = services.handle_resolver
        services.fs_service_registry.register_type(
            htypes.fs.local_fs_service, LocalFsService.from_data, services.ref_registry)
        fs_service = htypes.fs.local_fs_service()
        fs_service_ref = ref_registry.register_object(fs_service)
        home_path = os.path.expanduser('~').split('/')[1:]
        object = htypes.fs.fs(fs_service_ref, LOCAL_HOST_NAME, home_path, current_file_name=None)
        self._home_fs_ref = ref_registry.register_object(object)

    @command('open_local_fs')
    async def open_local_fs(self):
        return (await self._handle_resolver.resolve(self._home_fs_ref))
