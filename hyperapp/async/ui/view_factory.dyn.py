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

    async def create_view(self, object, add_dir_list=None):
        log.info("View factory: create view for object: %r; dirs: %s + %s", object, object.dir_list, add_dir_list)
        piece = self.pick_view_piece(object, add_dir_list)
        return await self._view_registry.animate(piece, object, add_dir_list)

    def pick_view_piece(self, object, add_dir_list=None):
        dir_list = list(dir_seq(
            object.dir_list + (add_dir_list or [])))
        return self._lcs.get_first(dir_list)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.view_factory = ViewFactory(services.lcs, services.view_registry)
