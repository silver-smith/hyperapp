import threading
from collections.abc import Hashable

from hyperapp.boot.code_registry import CodeRegistry


class CachedCodeRegistry(CodeRegistry):

    def __init__(self, mosaic, pyobj_creg, web, service_name, config):
        super().__init__(pyobj_creg, web, service_name, config)
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
            self._add_to_cache(piece, actor)
        return actor

    def actor_to_piece(self, actor, reconstruct=True):
        if isinstance(actor, Hashable):
            key = actor
        else:
            key = id(actor)
        try:
            return self._reverse_cache[key]
        except KeyError as x:
            raise KeyError(f"{self._service_name}: Missing actor {x} for: {actor!r}") from x

    def actor_to_piece_opt(self, actor, reconstruct=True):
        if actor is None:
            return None
        return self.actor_to_piece(actor, reconstruct)

    def actor_to_ref(self, actor, reconstruct=True):
        piece = self.actor_to_piece(actor, reconstruct)
        return self._mosaic.put(piece)

    def actor_to_ref_opt(self, actor, reconstruct=True):
        if actor is None:
            return None
        return self.actor_to_ref(actor, reconstruct)

    def add_to_cache(self, piece, actor):
        with self._lock:
            self._add_to_cache(piece, actor)

    def _add_to_cache(self, piece, actor):
        self._cache[piece] = actor
        if isinstance(actor, Hashable):
            self._reverse_cache[actor] = piece
        else:
            self._reverse_cache[id(actor)] = piece
            self._actor_keep.append(actor)
