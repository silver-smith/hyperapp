import logging

from .htypes import ref_t
from .htypes.deduce_value_type import deduce_value_type

_log = logging.getLogger(__name__)


class CodeRegistry2:

    def __init__(self, web, produce_name, config):
        super().__init__()
        self._web = web
        self._produce_name = produce_name
        self._config = config  # t -> fn

    def invite(self, ref, *args, **kw):
        assert isinstance(ref, ref_t), repr(ref)
        value, t = self._web.summon_with_t(ref)
        return self._animate(t, value, args, kw)

    def animate(self, piece, *args, **kw):
        t = deduce_value_type(piece)
        return self._animate(t, piece, args, kw)

    def _animate(self, t, piece, args, kw):
        try:
            fn = self._config[t]
        except KeyError:
            raise RuntimeError(f"No code is registered for {self._produce_name}: {t!r}; piece: {piece}")
        _log.debug('Producing %s for %s of type %s using %s(%s, %s)',
                   self._produce_name, piece, t, fn, args, kw)
        result = fn(piece, *args, **kw)
        _log.debug('Animated %s: %s to %s', self._produce_name, piece, str(result))
        return result
