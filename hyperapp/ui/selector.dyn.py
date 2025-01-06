from .services import (
    pyobj_creg,
    web,
    )
from .code.mark import mark


class Selector:

    def __init__(self, get_fn, pick_fn):
        self.get_fn = get_fn
        self.pick_fn = pick_fn


class SelectorTemplate:

    @classmethod
    @mark.actor.cfg_item_creg
    def from_piece(cls, piece):
        return cls(
            value_t=pyobj_creg.invite(piece.value_t),
            get_fn=web.summon(piece.get_fn),
            pick_fn=web.summon(piece.pick_fn),
            )

    def __init__(self, value_t, get_fn, pick_fn):
        self._value_t = value_t
        self._get_fn = get_fn
        self._pick_fn = pick_fn

    @property
    def key(self):
        return self._value_t

    def resolve(self, system, service_name):
        system_fn_creg = system.resolve_service('system_fn_creg')
        return Selector(
            get_fn=system_fn_creg.animate(self._get_fn),
            pick_fn=system_fn_creg.animate(self._pick_fn),
            )


@mark.service
def selector_reg(config):
    return config
