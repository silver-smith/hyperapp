import logging

log = logging.getLogger(__name__)


class LCSheet:

    def __init__(self, storage):
        self._storage = storage

    def get(self, dir):
        return self._storage.get(dir)

    def set(self, dir, piece):
        log.info("LCS: set%s %s -> %s", '/persist' if persist else '', set(dir), piece)
        self._storage.set(dir, piece)
