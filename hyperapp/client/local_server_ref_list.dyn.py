from ..common.interface import hyper_ref as href_types
from .command import command
from .module import Module


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._ref_resolver = services.ref_resolver

    @command('open_local_server')
    async def open_local_server(self):
        ref = b'server-ref-list'
        return (await self._ref_resolver.resolve_ref_to_handle(ref))
