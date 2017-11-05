import asyncio
from ..common.interface import hyper_ref as href_types
from .module import Module


class FsService(object):

    def __init__(self, remote_url):
        self._remote_url = remote_url


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._href_resolver = services.href_resolver
        self._service_registry = services.service_registry
        services.href_object_registry.register(href_types.fs_ref.id, self.resolve_fs_object)
        services.service_registry.register(href_types.fs_service.id, self.resolve_fs_service)

    @asyncio.coroutine
    def resolve_fs_object(self, fs_object):
        service_object = yield from self._href_resolver.resolve_service_ref(fs_object.fs_service_ref)
        fs_service = self._service_registry.resolve(service_object)
        assert False, repr((fs_object, fs_service))

    def resolve_fs_service(self, service_object):
        return FsService(service_object.remote_url)
