import threading

from hyperapp.common.code_registry2 import CodeRegistry2


class CachedCodeRegistry(CodeRegistry2):

    def __init__(self, mosaic, web, service_name, config):
        super().__init__(web, service_name, config)
        self._mosaic = mosaic
        self._actor_keep = []
        self._cache = {}  # piece -> actor
        self._reverse_cache = {}  # actor id -> piece
        self._lock = threading.Lock()

    # Disable additional *args and **kw because they make cache incorrect.
    def invite(self, ref):
        return super().invite(ref)

    def animate(self, piece):
        return super().animate(piece)

    def _animate(self, t, piece, args, kw):
        try:
            return self._cache[piece]
        except KeyError:
            pass
        actor = super()._animate(t, piece, args, kw)
        with self._lock:
            assert piece not in self._cache  # Ensure it is not yet added.
            self._cache[piece] = actor
            self._reverse_cache[id(actor)] = piece
            self._actor_keep.append(actor)
            return actor

    def actor_to_piece(self, actor, reconstruct=True):
        try:
            return self._reverse_cache[id(actor)]
        except KeyError as x:
            raise KeyError(f"{x}: {actor!r}") from x

    def actor_to_ref(self, actor, reconstruct=True):
        piece = self.actor_to_piece(actor, reconstruct)
        return self._mosaic.put(piece)

    def add_to_cache(self, piece, actor):
        with self._lock:
            self._cache[piece] = actor
            self._reverse_cache[id(actor)] = piece
            self._actor_keep.append(actor)
