import logging

from . import htypes
from .module import ClientModule

log = logging.getLogger(__name__)


def dir_seq(dir_list):
    for dir in dir_list:
        yield [htypes.view.view_d('default'), *dir]
        yield [htypes.view.view_d('selected'), *dir]


class ViewFactory:

    def __init__(self, lcs, view_registry):
        self._lcs = lcs
        self._view_registry = view_registry

    async def create_view(self, object, dir_list=None):
        if dir_list is None:
            dir_list = object.dir_list
        log.info("View factory: create view for object: %r; dirs: %s", object, dir_list)
        piece = self.pick_view_piece(dir_list)
        return await self._view_registry.animate(piece, object)

    def pick_view_piece(self, dir_list):
        selected_and_default_dir_list = list(dir_seq(dir_list))
        return self._lcs.get_first(selected_and_default_dir_list)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.view_factory = ViewFactory(services.lcs, services.view_registry)
