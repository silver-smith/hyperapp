from functools import partial

from . import htypes
from .services import pyobj_creg
from .code.mark import mark


class ContextFn:

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece, system):
        service_kw = {
            name: system.resolve_service(name)
            for name in piece.service_params
            }
        fn = pyobj_creg.invite(piece.function)
        bound_fn = partial(fn, **service_kw)
        return cls(piece.ctx_params, piece.service_params, fn, bound_fn)

    def __init__(self, ctx_params, service_params, fn, bound_fn):
        self._ctx_params = ctx_params
        self._service_params = service_params
        self._fn = fn
        self._bound_fn = bound_fn

    @property
    def piece(self):
        return htypes.system_fn.ctx_fn(
            function=pyobj_creg.actor_to_ref(self._fn),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )

    def call(self, ctx):
        kw = self._ctx_kw(ctx)
        return self._bound_fn(**kw)

    def _ctx_kw(self, ctx):
        kw = {
            **ctx.as_dict(),
            'ctx': ctx,
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
        return {
            name: value
            for name, value in kw.items()
            if name in self._ctx_params
            }

