import logging

from . import htypes
from .module import ClientModule

log = logging.getLogger(__name__)


def dir_seq(dir_list):
    for dir in dir_list:
        yield [htypes.view.view_d('default'), *dir]
        yield [htypes.view.view_d('selected'), *dir]


class ViewProducer:

    def __init__(self, lcs, view_registry):
        self._lcs = lcs
        self._view_registry = view_registry

    async def create_view(self, object, add_dir_list=None):
        log.info("View producer: create view for object: %r; dirs: %s + %s", object, object.dir_list, add_dir_list)
        _, piece = self.pick_view_piece(object, add_dir_list)
        return await self._view_registry.animate(piece, object, add_dir_list)

    def pick_view_piece(self, object, add_dir_list=None):
        dir_seq_list = self._dir_seq_list(object, add_dir_list)
        try:
            return next(iter(self._iter_dir(dir_seq_list)))
        except StopIteration:
            raise KeyError(f"No view is registered for any of dirs: {dir_seq_list}")

    def iter_matched_pieces(self, object, add_dir_list=None):
        dir_seq_list = self._dir_seq_list(object, add_dir_list)
        yield from self._iter_dir(dir_seq_list)

    def _dir_seq_list(self, object, add_dir_list):
        dir_list = object.dir_list + (add_dir_list or [])
        return list(dir_seq(dir_list))

    def _iter_dir(self, dir_seq_list):
        for dir in reversed(dir_seq_list):
            value = self._lcs.get(dir)
            log.debug("View: %s -> %r", dir, value)
            if value is not None:
                yield (dir, value)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.view_producer = ViewProducer(services.lcs, services.view_registry)
