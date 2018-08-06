import logging

from ..common.interface import hyper_ref as href_types
from ..common.interface import fs as fs_types
from ..common.url import Url
from .module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'fs.remote'


class RemoteFsService(object):

    @classmethod
    async def from_data(cls, service_ref, unused_service, proxy_factory):
        proxy = await proxy_factory.from_ref(service_ref)
        return cls(proxy)

    def __init__(self, proxy):
        self._proxy = proxy

    def to_ref(self):
        return self._proxy.service_ref

    async def fetch_dir_contents(self, host, path, sort_column_id, from_key, desc_count, asc_count):
        fetch_request = fs_types.row_fetch_request(sort_column_id, from_key, desc_count, asc_count)
        result = await self._proxy.fetch_dir_contents(host, path, fetch_request)
        return result.chunk


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.fs_service_registry.register(href_types.service, RemoteFsService.from_data, services.proxy_factory)
