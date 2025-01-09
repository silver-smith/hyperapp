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
from .code.command import BoundCommandBase, UnboundCommandBase

log = logging.getLogger(__name__)


class CrudOpenFn:

    _required_kw = {'model', 'current_item'}

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece, selector_reg):
        return cls(
            selector_reg=selector_reg,
            name=piece.name,
            value_t=pyobj_creg.invite(piece.value_t),
            key_fields=piece.key_fields,
            init_action_fn_ref=piece.init_action_fn,
            commit_command_d_ref=piece.commit_command_d,
            commit_action_fn_ref=piece.commit_action_fn,
            )

    def __init__(self, selector_reg, name, value_t, key_fields, init_action_fn_ref, commit_command_d_ref, commit_action_fn_ref):
        self._selector_reg = selector_reg
        self._name = name
        self._value_t = value_t
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
        try:
            selector = self._selector_reg[self._value_t]
        except KeyError:
            get_fn = None
            pick_fn = None
        else:
            get_fn = selector.get_fn
            pick_fn = selector.pick_fn
        return htypes.crud.model(
            value_t=pyobj_creg.actor_to_ref(self._value_t),
            model=mosaic.put(model),
            keys=keys,
            key_fields=self._key_fields,
            init_action_fn=self._init_action_fn_ref,
            commit_command_d=self._commit_command_d_ref,
            get_fn=mosaic.put(get_fn.piece) if get_fn else None,
            pick_fn=mosaic.put(pick_fn.piece) if pick_fn else None,
            commit_action_fn=self._commit_action_fn_ref,
            )


def _run_crud_init(ctx, system_fn_creg, crud_model):
    model = web.summon(crud_model.model)
    key_values = [web.summon(key) for key in crud_model.keys]
    keys_kw = {
        name: value
        for name, value in zip(crud_model.key_fields, key_values)
        }
    action_fn = system_fn_creg.invite(crud_model.init_action_fn)
    model_ctx = ctx.clone_with(
        piece=model,
        model=model,
        **keys_kw,
        )
    return action_fn.call(model_ctx)


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
        return self._init(ctx, ctx_kw['model'])

    def _init(self, ctx, crud_model):
        return _run_crud_init(ctx, self._system_fn_creg, crud_model)


def _form_view(value_t_ref):
    crud_init_fn = htypes.crud.init_fn()
    adapter = htypes.record_adapter.fn_record_adapter(
        record_t=value_t_ref,
        system_fn=mosaic.put(crud_init_fn),
        )
    return htypes.form.view(mosaic.put(adapter))


@mark.actor.model_layout_creg
def crud_model_layout(piece, lcs, ctx, system_fn_creg, visualizer, selector_reg):
    if not piece.get_fn:
        return _form_view(piece.value_t)
    get_fn = system_fn_creg.invite(piece.get_fn)
    value = _run_crud_init(ctx, system_fn_creg, piece)
    selector_model = get_fn.call(ctx, value=value)
    return visualizer(lcs, ctx, selector_model)


class UnboundCrudCommitCommand(UnboundCommandBase):

    def __init__(self, d, key_fields, keys, pick_fn, commit_fn):
        super().__init__(d)
        self._key_fields = key_fields
        self._keys = keys
        self._pick_fn = pick_fn
        self._commit_fn = commit_fn

    @property
    def properties(self):
        return htypes.command.properties(
            is_global=False,
            uses_state=False,
            remotable=False,
            )

    def bind(self, ctx):
        return BoundCrudCommitCommand(self._d, self._key_fields, self._keys, self._pick_fn, self._commit_fn, ctx)


class BoundCrudCommitCommand(BoundCommandBase):

    def __init__(self, d, key_fields, keys, pick_fn, commit_fn, ctx):
        super().__init__(d)
        self._key_fields = key_fields
        self._keys = keys
        self._pick_fn = pick_fn
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
        required_kw = {'model'}
        if not self._pick_fn:
            required_kw |= {'input'}
        return required_kw - self._ctx.as_dict().keys()

    async def run(self):
        crud_model = self._ctx.model
        model = web.summon(crud_model.model)
        if self._pick_fn:
            model_ctx = self._ctx.clone_with(piece=model, model=model)
            value = self._pick_fn.call(model_ctx)
        else:
            value = self._pick_ctx_value(self._ctx)
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

    @staticmethod
    def _pick_ctx_value(ctx):
        try:
            return ctx.value
        except KeyError:
            input = ctx.input
            return input.get_value()


@mark.command_enum
def crud_model_commands(piece, system_fn_creg):
    command_d = web.summon(piece.commit_command_d)
    keys = [web.summon(k) for k in piece.keys]
    pick_fn = system_fn_creg.invite_opt(piece.pick_fn)
    commit_fn = system_fn_creg.invite(piece.commit_action_fn)
    return [UnboundCrudCommitCommand(command_d, piece.key_fields, keys, pick_fn, commit_fn)]
