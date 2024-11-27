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
        return cls(
            name=piece.name,
            record_t_ref=piece.record_t,
            key_field=piece.key_field,
            init_action_fn_ref=piece.init_action_fn,
            commit_action=piece.commit_action,
            )

    def __init__(self, name, record_t_ref, key_field, init_action_fn_ref, commit_action):
        self._name = name
        self._record_t_ref = record_t_ref
        self._key_field = key_field
        self._init_action_fn_ref = init_action_fn_ref
        self._commit_action = commit_action

    def __repr__(self):
        return f"<CrudOpenFn {self._name} key={self._key_field})>"

    def missing_params(self, ctx, **kw):
        ctx_kw = {**ctx.as_dict(), **kw}
        return self._required_kw - ctx_kw.keys()

    def call(self, ctx, **kw):
        ctx_kw = {**ctx.as_dict(), **kw}
        return self._open(ctx_kw['model'], ctx_kw['current_item'])

    def _open(self, model, current_item):
        key = getattr(current_item, self._key_field)
        return htypes.crud.model(
            record_t=self._record_t_ref,
            model=mosaic.put(model),
            key=mosaic.put(key),
            key_field=self._key_field,
            init_action_fn=self._init_action_fn_ref,
            commit_action=self._commit_action,
            )


class CrudInitFn:

    _required_kw = {'model'}

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece, system_fn_creg):
        return cls(system_fn_creg)

    def __init__(self, system_fn_creg):
        self._system_fn_creg = system_fn_creg

    def __repr__(self):
        return f"<CrudInitFn>"

    def missing_params(self, ctx, **kw):
        ctx_kw = {**ctx.as_dict(), **kw}
        return self._required_kw - ctx_kw.keys()

    def call(self, ctx, **kw):
        ctx_kw = {**ctx.as_dict(), **kw}
        return self._init(ctx_kw['model'])

    def _init(self, crud_model):
        model = web.summon(crud_model.model)
        key = web.summon(crud_model.key)
        action_fn = self._system_fn_creg.invite(crud_model.init_action_fn)
        ctx = Context(
            piece=model,
            model=model,
            **{crud_model.key_field: key},
            )
        return action_fn.call(ctx)


@mark.actor.model_layout_creg
def crud_model_layout(piece, system_fn_creg):
    crud_init_fn = htypes.crud.init_fn()
    adapter = htypes.record_adapter.fn_record_adapter(
        record_t=piece.record_t,
        system_fn=mosaic.put(crud_init_fn),
        )
    return htypes.form.view(mosaic.put(adapter))
