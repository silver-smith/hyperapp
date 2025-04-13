from functools import partial

from . import htypes
from .services import pyobj_creg
from .code.mark import mark
from .code.rpc_call import DEFAULT_TIMEOUT


class ContextFn:

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece, system, rpc_system_call_factory):
        fn = pyobj_creg.invite(piece.function)
        bound_fn = system.bind_services(fn, piece.service_params)
        return cls(rpc_system_call_factory, piece.ctx_params, piece.service_params, fn, bound_fn)

    def __init__(self, rpc_system_call_factory, ctx_params, service_params, raw_fn, bound_fn=None):
        self._rpc_system_call_factory = rpc_system_call_factory
        self._ctx_params = ctx_params
        self._service_params = service_params
        self._raw_fn = raw_fn
        self._bound_fn = bound_fn  # Can be None if we use this only to create it's piece.

    def __repr__(self):
        return f"<ContextFn: {self._raw_fn}({self._ctx_params}/{self._service_params})>"

    @property
    def piece(self):
        return htypes.system_fn.ctx_fn(
            function=pyobj_creg.actor_to_ref(self._raw_fn),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )

    def call(self, ctx, **kw):
        ctx_kw = self._fn_kw(ctx, kw)
        return self._bound_fn(**ctx_kw)

    def fn_kw(self, ctx, **kw):
        return {
            **self._ctx_kw(ctx),
            **kw,
            'ctx': ctx,
            }

    @property
    def ctx_params(self):
        return self._ctx_params

    def missing_params(self, ctx, **kw):
        fn_kw = self.fn_kw(ctx, **kw)
        return self._ctx_params_set - fn_kw.keys()

    @property
    def _ctx_params_set(self):
        return set(self._ctx_params)

    def _fn_kw(self, ctx, additional_kw):
        fn_kw = self.fn_kw(ctx, **additional_kw)
        missing_params = self._ctx_params_set - fn_kw.keys()
        if missing_params:
            missing_str = ", ".join(missing_params)
            raise RuntimeError(f"{self._raw_fn}: Required parameters not provided: {missing_str}")
        return {
            name: fn_kw[name]
            for name in self._ctx_params
            }

    def _ctx_kw(self, ctx):
        kw = {
            **ctx.as_dict(),
            }
        if not {'widget', 'state'} & self._ctx_params_set:
            return kw
        try:
            view = ctx.view
        except KeyError:
            return kw
        try:
            widget = ctx.widget()
        except KeyError:
            return kw
        if widget is None:
            raise RuntimeError(f"{self!r}: widget is gone")
        kw['widget'] = widget
        if 'state' in self._ctx_params_set:
            kw['state'] = view.widget_state(widget)
        return kw

    def rpc_call(self, receiver_peer, sender_identity, ctx, timeout_sec=DEFAULT_TIMEOUT, **kw):
        rpc_call = self._rpc_system_call_factory(
            receiver_peer=receiver_peer,
            sender_identity=sender_identity,
            fn=self,
            )
        ctx_kw = self._fn_kw(ctx, kw)
        return rpc_call(**ctx_kw)
