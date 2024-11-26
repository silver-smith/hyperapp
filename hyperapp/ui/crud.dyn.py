from . import htypes
from .services import (
    deduce_t,
    mosaic,
    web,
    )
from .code.mark import mark
from .code.context import Context


class CrudOpenFn:

    _required_kw = {'model', 'current_item'}

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece):
        return cls(piece.name, piece.key_field, piece.init_action_fn, piece.commit_action)

    def __init__(self, name, key_field, init_action_fn, commit_action):
        self._name = name
        self._key_field = key_field
        self._init_action_fn = init_action_fn
        self._commit_action = commit_action

    def __repr__(self):
        return f"<CrudOpenFn {self._name} key={self._key_field})>"

    def call(self, ctx, **kw):
        ctx_kw = {**ctx.as_dict(), **kw}
        return self._open(ctx_kw['model'], ctx_kw['current_item'])

    def missing_params(self, ctx, **kw):
        ctx_kw = {**ctx.as_dict(), **kw}
        return self._required_kw - ctx_kw.keys()

    def _open(self, model, current_item):
        key = getattr(current_item, self._key_field)
        return htypes.crud.model(
            model=mosaic.put(model),
            key=mosaic.put(key),
            key_field=self._key_field,
            init_action_fn=self._init_action_fn,
            commit_action=self._commit_action,
            )


@mark.actor.model_layout_creg
def crud_model_layout(piece, system_fn_creg):
    model = web.summon(piece.model)
    key = web.summon(piece.key)
    model_t = deduce_t(model)
    fn = system_fn_creg.invite(piece.init_action_fn)
    action_ctx = Context(
        piece=model,
        model=model,
        **{piece.key_field: key},
        )
    return fn.call(action_ctx)
