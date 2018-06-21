import logging
from .module import ClientModule

log = logging.getLogger(__name__)


REDIRECT_VIEW_ID = 'ref_redirect'


def register_views(registry, services):
    registry.register(REDIRECT_VIEW_ID, this_module.resolve_redirect)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(services)
        self._handle_resolver = services.handle_resolver

    async def resolve_redirect(self, locale, handle, parent):
        return (await self._handle_resolver.resolve(handle.ref))
