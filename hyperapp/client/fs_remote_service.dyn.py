import logging

from ..common.interface import fs as fs_types
from ..common.url import Url
from .module import Module

log = logging.getLogger(__name__)


class RemoteFsService(object):

    @classmethod
    def from_data(cls, service_object, iface_registry, ref_registry, proxy_factory):
        service_url = Url.from_data(iface_registry, service_object.service_url)
        service_proxy = proxy_factory.from_url(service_url)
        return cls(ref_registry, service_proxy)

    def __init__(self, ref_registry, service_proxy):
        self._ref_registry = ref_registry
        self._service_proxy = service_proxy

    def to_data(self):
        service_url = self._service_proxy.get_url()
        return fs_types.remote_fs_service(service_url.to_data())

    def to_ref(self):
        service_object = self.to_data()
        return self._ref_registry.register_new_object(fs_types.remote_fs_service, service_object)

    async def fetch_dir_contents(self, host, path, sort_column_id, from_key, desc_count, asc_count):
        fetch_request = fs_types.row_fetch_request(sort_column_id, from_key, desc_count, asc_count)
        result = await self._service_proxy.fetch_dir_contents(host, path, fetch_request)
        return result.chunk


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        services.fs_service_registry.register(
            fs_types.remote_fs_service, RemoteFsService.from_data, services.iface_registry, services.ref_registry, services.proxy_factory)
