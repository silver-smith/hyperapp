from functools import partial

from . import htypes
from .services import pyobj_creg
from .code.mark import mark


class ContextFn:

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece, system, partial_ref):
        service_kw = {
            name: system.resolve_service(name)
            for name in piece.service_params
            }
        fn = pyobj_creg.invite(piece.function)
        bound_fn = partial(fn, **service_kw)
        return cls(partial_ref, piece.ctx_params, piece.service_params, fn, bound_fn)

    def __init__(self, partial_ref, ctx_params, service_params, unbound_fn, bound_fn):
        self._partial_ref = partial_ref
        self._ctx_params = ctx_params
        self._service_params = service_params
        self._unbound_fn = unbound_fn
        self._bound_fn = bound_fn

    def __repr__(self):
        return f"<ContextFn: {self._unbound_fn}({self._ctx_params}/{self._service_params})>"

    @property
    def piece(self):
        return htypes.system_fn.ctx_fn(
            function=pyobj_creg.actor_to_ref(self._unbound_fn),
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

    def missing_params(self, ctx, **kw):
        fn_kw = self.fn_kw(ctx, **kw)
        return set(self._ctx_params) - fn_kw.keys()

    def _fn_kw(self, ctx, additional_kw):
        fn_kw = self.fn_kw(ctx, **additional_kw)
        missing_params = set(self._ctx_params) - fn_kw.keys()
        if missing_params:
            missing_str = ", ".join(missing_params)
            raise RuntimeError(f"{self._unbound_fn}: Required parameters not provided: {missing_str}")
        return {
            name: fn_kw[name]
            for name in self._ctx_params
            }

    def _ctx_kw(self, ctx):
        kw = {
            **ctx.as_dict(),
            }
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
        kw['state'] = view.widget_state(widget)
        return kw

    def partial_ref(self, ctx, **kw):
        assert not self._service_params  # TODO: Remote call for system fn with service params.
        ctx_kw = self._fn_kw(ctx, kw)
        return self._partial_ref(self._unbound_fn, **ctx_kw)
