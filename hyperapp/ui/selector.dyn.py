from .services import (
    pyobj_creg,
    web,
    )
from .code.mark import mark


class Selector:

    def __init__(self, model_t, get_fn, pick_fn):
        self.model_t = model_t
        self.get_fn = get_fn
        self.pick_fn = pick_fn


class SelectorTemplate:

    @classmethod
    @mark.actor.cfg_item_creg
    def from_piece(cls, piece):
        return cls(
            value_t=pyobj_creg.invite(piece.value_t),
            model_t=pyobj_creg.invite(piece.model_t),
            get_fn=web.summon(piece.get_fn),
            pick_fn=web.summon(piece.pick_fn),
            )

    def __init__(self, value_t, model_t, get_fn, pick_fn):
        self._value_t = value_t
        self._model_t = model_t
        self._get_fn = get_fn
        self._pick_fn = pick_fn

    @property
    def key(self):
        return self._value_t

    def resolve(self, system, service_name):
        system_fn_creg = system.resolve_service('system_fn_creg')
        return Selector(
            model_t=self._model_t,
            get_fn=system_fn_creg.animate(self._get_fn),
            pick_fn=system_fn_creg.animate(self._pick_fn),
            )


class SelectorRegistry:

    def __init__(self, config):
        self._config = config

    def __getitem__(self, value_t):
        return self._config[value_t]

    def by_model_t(self, model_t):
        for selector in self._config.values():
            if selector.model_t is model_t:
                return selector
        raise KeyError(model_t)


@mark.service
def selector_reg(config):
    return SelectorRegistry(config)
