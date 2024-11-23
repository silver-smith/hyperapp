from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark


class CrudOpenFn:

    _required_kw = {'model', 'current_item'}

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece):
        return cls(piece.name, piece.key_field, piece.init_action, piece.commit_action)

    def __init__(self, name, key_field, init_action, commit_action):
        self._name = name
        self._key_field = key_field
        self._init_action = init_action
        self._commit_action = commit_action

    def __repr__(self):
        return f"<CrudOpenFn {self._name}: {self._key_field}/{self._init_action}/{self._commit_action})>"

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
            init_action=self._init_action,
            commit_action=self._commit_action,
            )


@mark.service
def crud_action_reg(config, model_t, action):
    return config[model_t, action]


@mark.actor.model_layout_creg
def crud_model_layout(piece, crud_action_reg):
    return ['sample']
