import logging
from functools import cached_property

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
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
            key_fields=piece.key_fields,
            init_action_fn_ref=piece.init_action_fn,
            commit_command_d_ref=piece.commit_command_d,
            commit_action_fn_ref=piece.commit_action_fn,
            )

    def __init__(self, name, value_t_ref, key_fields, init_action_fn_ref, commit_command_d_ref, commit_action_fn_ref):
        self._name = name
        self._value_t_ref = value_t_ref
        self._key_fields = key_fields
        self._init_action_fn_ref = init_action_fn_ref
        self._commit_command_d_ref = commit_command_d_ref
        self._commit_action_fn_ref = commit_action_fn_ref

    def __repr__(self):
        return f"<CrudOpenFn {self._name} keys={self._key_fields})>"

    def missing_params(self, ctx, **kw):
        ctx_kw = {**ctx.as_dict(), **kw}
        return self._required_kw - ctx_kw.keys()

    def call(self, ctx, **kw):
        ctx_kw = {**ctx.as_dict(), **kw}
        return self._open(ctx_kw['model'], ctx_kw['current_item'])

    def _open(self, model, current_item):
        keys = tuple(
            mosaic.put(getattr(current_item, name))
            for name in self._key_fields
            )
        return htypes.crud.model(
            value_t=self._value_t_ref,
            model=mosaic.put(model),
            keys=keys,
            key_fields=self._key_fields,
            init_action_fn=self._init_action_fn_ref,
            commit_command_d=self._commit_command_d_ref,
            commit_action_fn=self._commit_action_fn_ref,
            )


def _run_crud_init(system_fn_creg, crud_model):
    model = web.summon(crud_model.model)
    key_values = [web.summon(key) for key in crud_model.keys]
    keys_kw = {
        name: value
        for name, value in zip(crud_model.key_fields, key_values)
        }
    action_fn = system_fn_creg.invite(crud_model.init_action_fn)
    ctx = Context(
        piece=model,
        model=model,
        **keys_kw,
        )
    return action_fn.call(ctx)


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
        return _run_crud_init(self._system_fn_creg, crud_model)


def _form_view(value_t_ref):
    crud_init_fn = htypes.crud.init_fn()
    adapter = htypes.record_adapter.fn_record_adapter(
        record_t=value_t_ref,
        system_fn=mosaic.put(crud_init_fn),
        )
    return htypes.form.view(mosaic.put(adapter))


def _pick_ctx_value(ctx):
    try:
        return ctx.value
    except KeyError:
        input = ctx.input
        return input.get_value()


@mark.actor.model_layout_creg
def crud_model_layout(piece, lcs, ctx, system_fn_creg, visualizer, selector_reg):
    value_t = pyobj_creg.invite(piece.value_t)
    try:
        selector = selector_reg[value_t]
    except KeyError:
        return _form_view(piece.value_t)
    value = _run_crud_init(system_fn_creg, piece)
    selector_model = selector.get_fn.call(ctx, value=value)
    return visualizer(lcs, ctx, selector_model)


class UnboundCrudCommitCommand(UnboundCommandBase):

    def __init__(self, d, key_fields, keys, commit_fn):
        super().__init__(d)
        self._key_fields = key_fields
        self._keys = keys
        self._commit_fn = commit_fn

    @property
    def properties(self):
        return htypes.command.properties(
            is_global=False,
            uses_state=False,
            remotable=False,
            )

    def bind(self, ctx):
        return BoundCrudCommitCommand(self._d, self._key_fields, self._keys, self._commit_fn, ctx)


class BoundCrudCommitCommand(BoundCommandBase):

    _required_kw = {'model', 'input'}

    def __init__(self, d, key_fields, keys, commit_fn, ctx):
        super().__init__(d)
        self._key_fields = key_fields
        self._keys = keys
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
        value = _pick_ctx_value(self._ctx)
        log.info("Run CRUD commit command %r: %s=%r; value=%r", self.name, self._key_fields, self._keys, value)
        keys_kw = {
            name: value
            for name, value in zip(self._key_fields, self._keys)
            }
        ctx = self._ctx.clone_with(
            piece=model,
            model=model,
            value=value,
            **keys_kw,
            )
        return self._commit_fn.call(ctx)


@mark.command_enum
def crud_model_commands(piece, system_fn_creg):
    command_d = web.summon(piece.commit_command_d)
    keys = [web.summon(k) for k in piece.keys]
    commit_fn = system_fn_creg.invite(piece.commit_action_fn)
    return [UnboundCrudCommitCommand(command_d, piece.key_fields, keys, commit_fn)]
