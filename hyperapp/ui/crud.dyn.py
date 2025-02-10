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
        return f"<CrudOpenFn {self._name} keys={self._key_fields}>"

    def missing_params(self, ctx, **kw):
        ctx_kw = {**ctx.as_dict(), **kw}
        return self._required_kw - ctx_kw.keys()

    def call(self, ctx, **kw):
        ctx_kw = {**ctx.as_dict(), **kw}
        return self._open(ctx_kw['model'], ctx_kw['current_item'])

    def _open(self, model, current_item):
        try:
            selector = self._selector_reg[self._value_t]
        except KeyError:
            get_fn = None
            pick_fn = None
        else:
            get_fn = selector.get_fn
            pick_fn = selector.pick_fn
        args = tuple(
            htypes.crud.arg(
                name=name,
                value=mosaic.put(getattr(current_item, name)),
                )
            for name in self._key_fields
            )
        return htypes.crud.model(
            value_t=pyobj_creg.actor_to_ref(self._value_t),
            model=mosaic.put(model),
            args=args,
            init_action_fn=self._init_action_fn_ref,
            commit_command_d=self._commit_command_d_ref,
            get_fn=mosaic.put(get_fn.piece) if get_fn else None,
            pick_fn=mosaic.put(pick_fn.piece) if pick_fn else None,
            commit_action_fn=self._commit_action_fn_ref,
            commit_value_field='value',
            )


def _fn_ctx(ctx, crud_model, **kw):
    model = web.summon_opt(crud_model.model)
    args_kw = {
        arg.name: web.summon(arg.value)
        for arg in crud_model.args
        }
    if model is not None:
        model_kw = {
            'piece': model,
            'model': model,
            }
    else:
        model_kw = {}
    return ctx.clone_with(
        **model_kw,
        **args_kw,
        **kw,
        )


def _run_crud_init(ctx, system_fn_creg, crud_model):
    fn = system_fn_creg.invite(crud_model.init_action_fn)
    fn_ctx = _fn_ctx(ctx, crud_model)
    return fn.call(fn_ctx)


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
        assert piece.init_action_fn  # Init action fn may be omitted only for selectors.
        return _form_view(piece.value_t)
    get_fn = system_fn_creg.invite(piece.get_fn)
    if piece.init_action_fn:
        value = _run_crud_init(ctx, system_fn_creg, piece)
    else:
        value = None
    selector_model = get_fn.call(ctx, value=value)
    return visualizer(lcs, ctx, selector_model)


class UnboundCrudCommitCommand(UnboundCommandBase):

    def __init__(self, d, args, pick_fn, commit_fn, commit_value_field):
        super().__init__(d)
        self._args = args
        self._pick_fn = pick_fn
        self._commit_fn = commit_fn
        self._commit_value_field = commit_value_field

    @property
    def properties(self):
        return htypes.command.properties(
            is_global=False,
            uses_state=False,
            remotable=False,
            )

    def bind(self, ctx):
        return BoundCrudCommitCommand(self._d, self._args, self._pick_fn, self._commit_fn, self._commit_value_field, ctx)


class BoundCrudCommitCommand(BoundCommandBase):

    def __init__(self, d, args, pick_fn, commit_fn, commit_value_field, ctx):
        super().__init__(d)
        self._args = args
        self._pick_fn = pick_fn
        self._commit_fn = commit_fn
        self._commit_value_field = commit_value_field
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
        if self._pick_fn:
            # TODO: Invite a method to retrieve proper selector model.
            # May be, add special wrapper view adding selector model to context when using selector.
            selector_model = None
            model_ctx = self._ctx.clone_with(piece=selector_model, model=selector_model)
            value = self._pick_fn.call(model_ctx)
        else:
            value = self._pick_ctx_value(self._ctx)
        log.info("Run CRUD commit command %r: args=%s; %s=%r", self.name, self._args, self._commit_value_field, value)
        fn_ctx = _fn_ctx(
            self._ctx,
            crud_model=self._ctx.model,
            **{self._commit_value_field: value},
            )
        return self._commit_fn.call(fn_ctx)

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
    args = {
        arg.name: web.summon(arg.value)
        for arg in piece.args
        }
    pick_fn = system_fn_creg.invite_opt(piece.pick_fn)
    commit_fn = system_fn_creg.invite(piece.commit_action_fn)
    return [UnboundCrudCommitCommand(command_d, args, pick_fn, commit_fn, piece.commit_value_field)]
