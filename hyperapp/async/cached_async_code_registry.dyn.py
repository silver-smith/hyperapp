from .code_registry import CodeRegistry


class CachedAsyncCodeRegistry(CodeRegistry):

    def __init__(self, produce_name, async_web, types):
        super().__init__(produce_name, async_web, types)
        self._cache = {}  # piece -> actor

    async def _animate(self, t, piece, args, kw):
        try:
            return self._cache[piece]
        except KeyError:
            pass
        actor = await super()._animate(t, piece, args, kw)
        self._cache[piece] = actor
        return actor
