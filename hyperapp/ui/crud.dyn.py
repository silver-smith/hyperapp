import logging
from functools import cached_property

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    web,
    )
from .code.mark import mark
from .code.context import Context
from .code.command import BoundCommandBase, UnboundCommandBase

log = logging.getLogger(__name__)


class CrudOpenFn:

    _required_kw = {'model', 'current_item'}

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece):
        return cls(
            name=piece.name,
            value_t_ref=piece.value_t,
            key_field=piece.key_field,
            init_action_fn_ref=piece.init_action_fn,
            commit_command_d_ref=piece.commit_command_d,
            commit_action_fn_ref=piece.commit_action_fn,
            )

    def __init__(self, name, value_t_ref, key_field, init_action_fn_ref, commit_command_d_ref, commit_action_fn_ref):
        self._name = name
        self._value_t_ref = value_t_ref
        self._key_field = key_field
        self._init_action_fn_ref = init_action_fn_ref
        self._commit_command_d_ref = commit_command_d_ref
        self._commit_action_fn_ref = commit_action_fn_ref

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
            value_t=self._value_t_ref,
            model=mosaic.put(model),
            key=mosaic.put(key),
            key_field=self._key_field,
            init_action_fn=self._init_action_fn_ref,
            commit_command_d=self._commit_command_d_ref,
            commit_action_fn=self._commit_action_fn_ref,
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
def crud_model_layout(piece, lcs, ctx, system_fn_creg):
    crud_init_fn = htypes.crud.init_fn()
    adapter = htypes.record_adapter.fn_record_adapter(
        record_t=piece.value_t,
        system_fn=mosaic.put(crud_init_fn),
        )
    return htypes.form.view(mosaic.put(adapter))


class UnboundCrudCommitCommand(UnboundCommandBase):

    def __init__(self, d, key_field, key, commit_fn):
        super().__init__(d)
        self._key_field = key_field
        self._key = key
        self._commit_fn = commit_fn

    @property
    def properties(self):
        return htypes.command.properties(
            is_global=False,
            uses_state=False,
            remotable=False,
            )

    def bind(self, ctx):
        return BoundCrudCommitCommand(self._d, self._key_field, self._key, self._commit_fn, ctx)


class BoundCrudCommitCommand(BoundCommandBase):

    _required_kw = {'model', 'input'}

    def __init__(self, d, key_field, key, commit_fn, ctx):
        super().__init__(d)
        self._key_field = key_field
        self._key = key
        self._commit_fn = commit_fn
        self._ctx = ctx

    @property
    def enabled(self):
        return not self._missing_params

    @property
    def disabled_reason(self):
        params = ", ".join(self._missing_params)
        return f"Params not ready: {params}"

    @cached_property
    def _missing_params(self):
        return self._required_kw - self._ctx.as_dict().keys()

    async def run(self):
        crud_model = self._ctx.model
        model = web.summon(crud_model.model)
        input = self._ctx.input
        value = input.get_value()
        log.info("Run CRUD commit command %r: %s=%r; value=%r", self.name, self._key_field, self._key, value)
        ctx = self._ctx.clone_with(
            piece=model,
            model=model,
            value=value,
            **{self._key_field: self._key},
            )
        return self._commit_fn.call(ctx)


@mark.command_enum
def crud_model_commands(piece, system_fn_creg):
    command_d = web.summon(piece.commit_command_d)
    key = web.summon(piece.key)
    commit_fn = system_fn_creg.invite(piece.commit_action_fn)
    return [UnboundCrudCommitCommand(command_d, piece.key_field, key, commit_fn)]
