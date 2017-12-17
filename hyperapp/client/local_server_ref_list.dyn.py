from ..common.interface import hyper_ref as href_types
from .command import command
from .module import Module


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._href_resolver = services.href_resolver

    @command('open_local_server')
    async def open_local_server(self):
        href = href_types.href('sha256', b'server-ref-list')
        return (await self._href_resolver.resolve_href_to_handle(href))
