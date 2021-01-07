import logging
import os.path

from hyperapp.client.module import ClientModule

from . import htypes
from .object_command import command
from .fs_service_impl import FsServiceImpl

log = logging.getLogger(__name__)

LOCAL_HOST_NAME = 'local'


class LocalFsService(object):

    @classmethod
    def from_data(cls, unused_local_fs_service, mosaic):
        return cls(mosaic)

    def __init__(self, mosaic):
        self._mosaic = mosaic
        self._impl = FsServiceImpl()

    def to_ref(self):
        local_fs_service = htypes.fs.local_fs_service()
        return self._mosaic.distil(local_fs_service)

    async def fetch_dir_contents(self, host, path, sort_column_id, from_key, desc_count, asc_count):
        assert host == LOCAL_HOST_NAME, repr(host)
        fetch_request = htypes.fs.row_fetch_request(sort_column_id, from_key, desc_count, asc_count)
        return self._impl.fetch_dir_contents(path, fetch_request)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)
        mosaic = services.mosaic
        services.fs_service_registry.register_actor(
            htypes.fs.local_fs_service, LocalFsService.from_data, services.mosaic)
        fs_service = htypes.fs.local_fs_service()
        fs_service_ref = mosaic.distil(fs_service)
        services.local_fs_service_ref = fs_service_ref
        # home_path = os.path.expanduser('~').split('/')[1:]
        home_path = ['usr', 'share']
        self._local_fs = local_fs = htypes.fs.fs(fs_service_ref, LOCAL_HOST_NAME, home_path, current_file_name=None)
        self._local_fs_ref = mosaic.distil(local_fs)

    @command('open_local_fs')
    async def open_local_fs(self):
        return self._local_fs

    @command('open_local_fs_list')
    async def open_local_fs_list(self):
        return htypes.tree_to_list_adapter.tree_to_list_adapter(self._local_fs_ref, self._local_fs.path)
