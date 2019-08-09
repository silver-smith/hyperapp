import logging

from hyperapp.common.url import Url
from hyperapp.client.module import ClientModule
from . import htypes

log = logging.getLogger(__name__)


class RemoteFsService(object):

    @classmethod
    async def from_data(cls, service, ref_registry, proxy_factory):
        service_ref = ref_registry.register_object(service)  # making duplicate/overwrite
        proxy = await proxy_factory.from_ref(service_ref)
        return cls(proxy)

    def __init__(self, proxy):
        self._proxy = proxy

    def to_ref(self):
        return self._proxy.service_ref

    async def fetch_dir_contents(self, host, path, sort_column_id, from_key, desc_count, asc_count):
        fetch_request = htypes.fs.row_fetch_request(sort_column_id, from_key, desc_count, asc_count)
        result = await self._proxy.fetch_dir_contents(host, path, fetch_request)
        return result.chunk


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.fs_service_registry.register_type(
            htypes.hyper_ref.service, RemoteFsService.from_data, services.ref_registry, services.proxy_factory)
