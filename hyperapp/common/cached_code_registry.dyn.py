from hyperapp.common.code_registry import CodeRegistry


class CachedCodeRegistry(CodeRegistry):

    def __init__(self, produce_name, web, types):
        super().__init__(produce_name, web, types)
        self._cache = {}  # piece -> actor

    def _animate(self, t, piece, args, kw):
        try:
            return self._cache[piece]
        except KeyError:
            pass
        actor = super()._animate(t, piece, args, kw)
        self._cache[piece] = actor
        return actor
