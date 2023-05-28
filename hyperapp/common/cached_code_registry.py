from hyperapp.common.code_registry import CodeRegistry


class CachedCodeRegistry(CodeRegistry):

    def __init__(self, produce_name, web, types):
        super().__init__(produce_name, web, types)
        self._cache = {}  # piece -> actor
        self._reverse_cache = {}  # actor id -> piece

    def _animate(self, t, piece, args, kw):
        try:
            return self._cache[piece]
        except KeyError:
            pass
        actor = super()._animate(t, piece, args, kw)
        self._cache[piece] = actor
        self._reverse_cache[id(actor)] = piece
        return actor

    def reverse_resolve(self, actor):
        return self._reverse_cache[id(actor)]
