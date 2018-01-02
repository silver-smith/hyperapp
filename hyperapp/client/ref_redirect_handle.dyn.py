import logging
from .module import Module

log = logging.getLogger(__name__)


REDIRECT_VIEW_ID = 'ref_redirect'


def register_views(registry, services):
    registry.register(REDIRECT_VIEW_ID, this_module.resolve_redirect)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._ref_resolver = services.ref_resolver

    async def resolve_redirect(self, locale, handle, parent):
        return (await self._ref_resolver.resolve_ref_to_handle(handle.ref))
