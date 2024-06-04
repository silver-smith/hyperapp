from hyperapp.common.code_registry import CodeRegistry


class CachedCodeRegistry(CodeRegistry):

    def __init__(self, mosaic, web, association_reg, pyobj_creg, produce_name):
        super().__init__(mosaic, web, association_reg, pyobj_creg, produce_name)
        self._cache = {}  # piece -> actor
        self._reverse_cache = {}  # actor id -> piece

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
        self._cache[piece] = actor
        self._reverse_cache[id(actor)] = piece
        return actor

    def actor_to_piece(self, actor):
        try:
            return self._reverse_cache[id(actor)]
        except KeyError as x:
            raise KeyError(f"{x}: {actor!r}")

    def actor_to_ref(self, actor):
        piece = self.actor_to_piece(actor)
        return self._mosaic.put(piece)

    def add_to_cache(self, piece, actor):
        self._cache[piece] = actor
        self._reverse_cache[id(actor)] = piece

