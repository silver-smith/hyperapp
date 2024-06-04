import inspect
import logging
from collections import namedtuple
from functools import cached_property

from .htypes import code_registry_ctr_t, ref_t
from .htypes.deduce_value_type import deduce_value_type
from .ref import decode_capsule
from .resource_ctr import add_fn_attr_constructor

_log = logging.getLogger(__name__)


class CodeRegistry:

    _Rec = namedtuple('_Rec', 'factory args kw')

    def __init__(self, mosaic, web, association_reg, pyobj_creg, produce_name):
        super().__init__()
        self._mosaic = mosaic
        self._web = web
        self._association_reg = association_reg
        self._pyobj_creg = pyobj_creg
        self._produce_name = produce_name
        self._registry = {}  # t -> _Rec

    def actor(self, t):
        def register(fn):
            type_ref = self._pyobj_creg.actor_to_ref(t)
            ctr = code_registry_ctr_t(
                service=self._mosaic.put(self._my_resource),
                type=type_ref,
                )
            add_fn_attr_constructor(fn, self._mosaic.put(ctr))
            return fn

        return register

    @cached_property
    def _my_resource(self):
        return self._pyobj_creg.actor_to_piece(self)

    def type_registered(self, t):
        if t in self._registry:
            return True
        t_res = self._pyobj_creg.actor_to_piece(t)
        return (self._my_resource, t_res) in self._association_reg

    def register_actor(self, t, factory, *args, **kw):
        assert not inspect.iscoroutinefunction(factory), f"Use client CodeRegistry for async factories: {factory!r}"
        _log.info('Register %s: %s -> %s(*%r, **%r)', self._produce_name, t, factory, args, kw)
        assert t not in self._registry, f"Duplicate {self._produce_name}: {t!r}"
        self._registry[t] = self._Rec(factory, args, kw)

    def invite(self, ref, *args, **kw):
        assert isinstance(ref, ref_t), repr(ref)
        value, t = self._web.summon_with_t(ref)
        return self._animate(t, value, args, kw)

    def animate(self, piece, *args, **kw):
        t = deduce_value_type(piece)
        return self._animate(t, piece, args, kw)

    def _resolve_record(self, t):
        try:
            return self._registry[t]
        except KeyError:
            if not self._association_reg:
                raise
        t_res = self._pyobj_creg.actor_to_piece(t)
        fn_res = self._association_reg[self._my_resource, t_res]
        try:
            fn = self._pyobj_creg.animate(fn_res)
            return self._Rec(fn, args=[], kw={})
        except KeyError as x:
            # Do not let KeyError out - it will be caught by superclass and incorrect error message will be produced.
            raise RuntimeError(f"{self._produce_name}: Error resolving function for {t!r}, {fn_res}: {x}")

    def _animate(self, t, piece, args, kw):
        try:
            rec = self._resolve_record(t)
        except KeyError:
            raise RuntimeError(f"No code is registered for {self._produce_name}: {t!r}; piece: {piece}")
        _log.debug('Producing %s for %s of type %s using %s(%s/%s, %s/%s)',
                   self._produce_name, piece, t, rec.factory, rec.args, args, rec.kw, kw)
        actor = rec.factory(piece, *args, *rec.args, **kw, **rec.kw)
        _log.debug('Animated %s: %s to %s', self._produce_name, piece, str(actor))
        return actor
