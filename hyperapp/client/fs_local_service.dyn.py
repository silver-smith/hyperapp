import logging
import os.path

from ..common.interface import fs as fs_types
from ..common.fs_service_impl import FsServiceImpl
from .command import command
from .module import Module

log = logging.getLogger(__name__)


LOCAL_HOST_NAME = 'local'


class LocalFsService(object):

    @classmethod
    def from_data(cls, service_object, ref_registry):
        return cls(ref_registry)

    def __init__(self, ref_registry):
        self._ref_registry = ref_registry
        self._impl = FsServiceImpl(fs_types)

    def to_data(self):
        return fs_types.local_fs_service()

    def to_ref(self):
        return self._ref_registry.register_new_object(fs_types.local_fs_service, self.to_data())

    async def fetch_dir_contents(self, host, path, sort_column_id, from_key, desc_count, asc_count):
        assert host == LOCAL_HOST_NAME, repr(host)
        fetch_request = fs_types.row_fetch_request(sort_column_id, from_key, desc_count, asc_count)
        return self._impl.fetch_dir_contents(path, fetch_request)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        ref_registry = services.ref_registry
        self._handle_resolver = services.handle_resolver
        services.fs_service_registry.register(
            fs_types.local_fs_service, LocalFsService.from_data, services.ref_registry)
        fs_service = fs_types.local_fs_service()
        fs_service_ref = ref_registry.register_new_object(fs_types.local_fs_service, fs_service)
        home_path = os.path.expanduser('~').split('/')[1:]
        object = fs_types.fs_ref(fs_service_ref, LOCAL_HOST_NAME, home_path)
        self._home_fs_ref = ref_registry.register_new_object(fs_types.fs_ref, object)

    @command('open_local_fs')
    async def open_local_fs(self):
        return (await self._handle_resolver.resolve(self._home_fs_ref))
