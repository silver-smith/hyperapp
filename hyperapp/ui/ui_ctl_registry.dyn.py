import logging
from functools import cached_property

from hyperapp.common.htypes import ref_t
from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.ref import decode_capsule

from .services import (
    association_reg,
    mark,
    pyobj_creg,
    types,
    web,
    )

log = logging.getLogger(__name__)


class UiCtlRegistry:

    _produce_name = 'ui_ctl'

    def __init__(self):
        self._cache = {}  # t -> actor

    @cached_property
    def _my_resource(self):
        return pyobj_creg.reverse_resolve(self)

    def invite(self, ref, *args, **kw):
        assert isinstance(ref, ref_t), repr(ref)
        capsule = web.pull(ref)
        decoded_capsule = decode_capsule(types, capsule)
        return self._animate(decoded_capsule.t, decoded_capsule.value, args, kw)

    def animate(self, piece, *args, **kw):
        t = deduce_value_type(piece)
        return self._animate(t, piece, args, kw)

    def _animate(self, t, piece, args, kw):
        try:
            factory = self._resolve_record(t)
        except KeyError:
            raise RuntimeError(f"No code is registered for {self._produce_name}: {t!r}; piece: {piece}")
        log.debug('Producing %s for %s of type %s using %s(%s, %s)',
                   self._produce_name, piece, t, factory, args, kw)
        actor = factory(piece, *args, **kw)
        log.debug('Animated %s: %s to %s', self._produce_name, piece, str(actor))
        return actor

    def _resolve_record(self, t):
        try:
            return self._cache[t]
        except KeyError:
            pass
        t_res = pyobj_creg.reverse_resolve(t)
        view = association_reg[self._my_resource, t_res]
        try:
            return pyobj_creg.invite(view.ctr_fn)
        except KeyError as x:
            raise RuntimeError(f"{self._produce_name}: Error resolving function for {t!r}, {fn_res}: {x}")


@mark.service
def ui_ctl_creg():
    return UiCtlRegistry()
