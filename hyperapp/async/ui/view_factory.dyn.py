import logging

from .module import ClientModule

log = logging.getLogger(__name__)


class ViewFactory:

    def __init__(self, lcs, view_registry):
        self._lcs = lcs
        self._view_registry = view_registry

    async def create_view(self, object, dir_list=None):
        if dir_list is None:
            dir_list = object.dir_list
        log.info("View factory: create view for object: %r; dirs: %s", object, dir_list)
        piece = self._lcs.get_first(dir_list)
        return await self._view_registry.animate(piece, object)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.view_factory = ViewFactory(services.lcs, services.view_registry)
