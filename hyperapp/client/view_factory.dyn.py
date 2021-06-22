from .module import ClientModule


class ViewFactory:

    def __init__(self, lcs, view_registry):
        self._lcs = lcs
        self._view_registry = view_registry

    async def create_view(self, object):
        piece = self._lcs.get(object.dir_list)
        return await self._view_registry.animate(piece, object)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.view_factory = ViewFactory(services.lcs, services.view_registry)
