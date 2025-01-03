from .services import (
    pyobj_creg,
    web,
    )
from .code.mark import mark


class Selector:

    def __init__(self, get_fn, put_fn):
        self.get_fn = get_fn
        self.put_fn = put_fn


class SelectorTemplate:

    @classmethod
    @mark.actor.cfg_item_creg
    def from_piece(cls, piece):
        return cls(
            value_t=pyobj_creg.invite(piece.value_t),
            get_fn=web.summon(piece.get_fn),
            put_fn=web.summon(piece.put_fn),
            )

    def __init__(self, value_t, get_fn, put_fn):
        self._value_t = value_t
        self._get_fn = get_fn
        self._put_fn = put_fn

    @property
    def key(self):
        return self._value_t

    def resolve(self, system, service_name):
        system_fn_creg = system.resolve_service('system_fn_creg')
        return Selector(
            get_fn=system_fn_creg.animate(self._get_fn),
            put_fn=system_fn_creg.animate(self._put_fn),
            )


@mark.service
def selector_reg(config):
    return config
