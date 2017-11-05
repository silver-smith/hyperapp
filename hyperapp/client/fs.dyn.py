import asyncio
from .module import Module


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._href_resolver = services.href_resolver
        self._service_registry = services.service_registry
        services.href_object_registry.register('fs_ref', self.resolve_fs_object)

    @asyncio.coroutine
    def resolve_fs_object(self, fs_object):
        service_object = yield from self._href_resolver.resolve_service_ref(fs_object.fs_service_ref)
        fs_service = self._service_registry.resolve(service_object)
        assert False, repr((fs_object, fs_service))
