import asyncio
from .module import Module


REDIRECT_VIEW_ID = 'href_redirect'


def register_views(registry, services):
    registry.register(REDIRECT_VIEW_ID, this_module.resolve_redirect)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._href_resolver = services.href_resolver
        self._href_object_registry = services.href_object_registry
        self._iface_registry = services.iface_registry
        self._remoting = services.remoting

    @asyncio.coroutine
    def resolve_redirect(self, locale, handle, parent):
        href = handle.href
        object = yield from self._href_resolver.resolve_href(href)
        assert object, repr(object)
        print(repr(object))
        handle = self._href_object_registry.resolve(object)
        assert handle, repr(handle)
        print(repr(handle))
        return handle
