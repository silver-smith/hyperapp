import logging
from collections import defaultdict

from .module import ClientModule

log = logging.getLogger(__name__)


class LCSheet:

    def __init__(self):
        self._dir_to_piece = defaultdict(list)

    def add(self, dir_list, piece):
        for dir in dir_list:
            log.info("LCS: add %s -> %s", dir, piece)
            self._dir_to_piece[tuple(dir)].append(piece)

    def set(self, dir_list, piece):
        for dir in dir_list:
            log.info("LCS: set %s -> %s", dir, piece)
            self._dir_to_piece[tuple(dir)] = [piece]

    def iter(self, dir_list):
        for dir in dir_list:
            yield from self._dir_to_piece[tuple(dir)]

    def get(self, dir_list):
        for dir in reversed(dir_list):
            piece_list = self._dir_to_piece[tuple(dir)]
            if len(piece_list) > 1:
                raise RuntimeError(f"More than one value is registered for {dir}")
            if piece_list:
                return piece_list[0]
        raise KeyError(f"No dir among {dir_list} is registered at LCS")


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.lcs = LCSheet()
