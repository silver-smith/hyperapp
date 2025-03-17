import logging

from .htypes import ref_t
from .htypes.deduce_value_type import deduce_value_type
from .config_item_missing import ConfigItemMissingError

_log = logging.getLogger(__name__)


class CodeRegistry:

    def __init__(self, web, service_name, config):
        super().__init__()
        self._web = web
        self._service_name = service_name
        self._config = config  # t -> fn

    def update_config(self, config):
        self._config.update(config)

    def invite(self, ref, *args, **kw):
        assert isinstance(ref, ref_t), repr(ref)
        value, t = self._web.summon_with_t(ref)
        return self._animate(t, value, args, kw)

    def invite_opt(self, ref, *args, **kw):
        if ref is None:
            return None
        return self.invite(ref, *args, **kw)

    def animate(self, piece, *args, **kw):
        t = deduce_value_type(piece)
        return self._animate(t, piece, args, kw)

    def animate_opt(self, piece, *args, **kw):
        if piece is None:
            return None
        return self.animate(piece, *args, **kw)

    def _animate(self, t, piece, args, kw):
        try:
            fn = self._config[t]
        except KeyError:
            raise ConfigItemMissingError(self._service_name, t, f"{self._service_name} actor is missing for: {t}")
        _log.debug('Producing %s actor for %s of type %s using %s(%s, %s)',
                   self._service_name, piece, t, fn, args, kw)
        result = self._call(fn, piece, args, kw)
        _log.debug('Animated %s actor: %s to %s', self._service_name, piece, str(result))
        return result

    def _call(self, fn, piece, args, kw):
        return fn(piece, *args, **kw)
