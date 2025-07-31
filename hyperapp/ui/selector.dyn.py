from .services import (
    pyobj_creg,
    )
from .code.mark import mark


class Selector:

    def __init__(self, model_t, get_fn, pick_fn):
        self.model_t = model_t
        self.get_fn = get_fn
        self.pick_fn = pick_fn


@mark.actor.cfg_value_creg
def resolve_selector_cfg_value(piece, key, system, service_name):
    system_fn_creg = system.resolve_service('system_fn_creg')
    return Selector(
        model_t=pyobj_creg.invite(piece.model_t),
        get_fn=system_fn_creg.invite(piece.get_fn),
        pick_fn=system_fn_creg.invite(piece.pick_fn),
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
