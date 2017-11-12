import asyncio
import logging
from .module import Module

log = logging.getLogger(__name__)


REDIRECT_VIEW_ID = 'href_redirect'


def register_views(registry, services):
    registry.register(REDIRECT_VIEW_ID, this_module.resolve_redirect)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._href_resolver = services.href_resolver

    @asyncio.coroutine
    def resolve_redirect(self, locale, handle, parent):
        return (yield from self._href_resolver.resolve_href_to_handle(handle.href))
