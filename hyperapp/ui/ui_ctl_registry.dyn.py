from hyperapp.common.htypes import ref_t
from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.ref import decode_capsule

from .services import (
    association_reg,
    mark,
    python_object_creg,
    types,
    web,
    )
from .code.dyn_code_registry import DynCodeRegistry


class UiCtlRegistry:

    _produce_name = 'ui_ctl'

    def __init__(self):
        self._cache = {}  # t -> actor

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
        _log.debug('Producing %s for %s of type %s using %s(%s, %s)',
                   self._produce_name, piece, t, factory, args, kw)
        actor = factory(piece, *args, **kw)
        _log.debug('Animated %s: %s to %s', self._produce_name, piece, str(actor))
        return actor

    def _resolve_record(self, t):
        try:
            return self._cache[t]
        except KeyError:
            pass
        fn_res = association_reg[self, t]
        try:
            return python_object_creg.invite(fn_res)
        except KeyError as x:
            # Do not let KeyError out - it will be caught by superclass and incorrect error message will be produced.
            raise RuntimeError(f"{self._produce_name}: Error resolving function for {t!r}, {fn_res}: {x}")


@mark.service
def ui_ctl_creg():
    return UiCtlRegistry()
