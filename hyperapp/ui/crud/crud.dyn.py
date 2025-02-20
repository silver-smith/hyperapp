import logging
import weakref
from functools import cached_property

from hyperapp.boot.htypes import TPrimitive

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.command import BoundCommandBase, UnboundCommandBase
from .code.ui_model_command import wrap_model_command_to_ui_command
from .code.context_view import ContextView

log = logging.getLogger(__name__)


def _args_dict_to_tuple(args):
    return tuple(
        htypes.crud.arg(name, mosaic.put(value))
        for name, value in args.items()
        )


def _args_tuple_to_dict(args):
    return {
        arg.name: web.summon(arg.value)
        for arg in args
        }


class CrudContextView(ContextView):

    @classmethod
    @mark.view
    def from_piece(cls, piece, ctx, system_fn_creg, view_reg, crud_helpers):
        base_view = view_reg.invite(piece.base_view, ctx)
        model = web.summon_opt(piece.model)
        command_d = web.summon(piece.commit_command_d)
        return cls(
            system_fn_creg, crud_helpers, base_view, piece.label, model,
            command_d, _args_tuple_to_dict(piece.args), piece.pick_fn, piece.commit_fn, piece.commit_value_field)

    def __init__(
            self, system_fn_creg, helpers, base_view, label, model,
            command_d, args, pick_fn_ref, commit_fn_ref, commit_value_field):
        super().__init__(base_view, label)
        self._system_fn_creg = system_fn_creg
        self._helpers = helpers
        self._model = model
        self._command_d = command_d
        self._args = args
        self._pick_fn_ref = pick_fn_ref
        self._commit_fn_ref = commit_fn_ref
        self._commit_value_field = commit_value_field

    @property
    def piece(self):
        return htypes.crud.view(
            base_view=mosaic.put(self._base_view.piece),
            label=self._label,
            model=mosaic.put_opt(self._model),
            commit_command_d=mosaic.put(self._command_d),
            args=_args_dict_to_tuple(self._args),
            pick_fn=self._pick_fn_ref,
            commit_fn=self._commit_fn_ref,
            commit_value_field=self._commit_value_field,
            )

    @property
    def unbound_commit_command(self):
        pick_fn = self._system_fn_creg.invite_opt(self._pick_fn_ref)
        commit_fn = self._system_fn_creg.invite(self._commit_fn_ref)
        return UnboundCrudCommitCommand(
            self._helpers, self._command_d, self._model, self._args, pick_fn, commit_fn, self._commit_value_field)


class CrudOpenFn:

    _required_kw = {'view', 'widget', 'navigator', 'model', 'current_item'}

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece, system_fn_creg, view_reg, selector_reg, crud_helpers):
        return cls(
            system_fn_creg=system_fn_creg,
            view_reg=view_reg,
            selector_reg=selector_reg,
            helpers=crud_helpers,
            name=piece.name,
            value_t=pyobj_creg.invite(piece.value_t),
            key_fields=piece.key_fields,
            init_action_fn_ref=piece.init_action_fn,
            commit_command_d_ref=piece.commit_command_d,
            commit_action_fn_ref=piece.commit_action_fn,
            )

    def __init__(
            self, system_fn_creg, view_reg, selector_reg, helpers,
            name, value_t, key_fields, init_action_fn_ref, commit_command_d_ref, commit_action_fn_ref):
        self._system_fn_creg = system_fn_creg
        self._view_reg = view_reg
        self._selector_reg = selector_reg
        self._helpers = helpers
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
        view = ctx_kw['view']
        widget_wr = ctx_kw['widget']
        widget = widget_wr()
        if widget is None:
            raise RuntimeError(f"{self!r}: widget is gone")
        return self._open(
            view=view,
            state=view.widget_state(widget),
            navigator_rec=ctx_kw['navigator'],
            model=ctx_kw['model'],
            current_item=ctx_kw['current_item'],
            ctx=ctx,
            )

    def _open(self, view, state, navigator_rec, model, current_item, ctx):
        try:
            selector = self._selector_reg[self._value_t]
        except KeyError:
            get_fn = None
            pick_fn = None
        else:
            get_fn = selector.get_fn
            pick_fn = selector.pick_fn
        args = {
            name: getattr(current_item, name)
            for name in self._key_fields
            }
        if not get_fn:
            # assert piece.init_action_fn  # Init action fn may be omitted only for selectors.
            new_model, base_view_piece = self._editor_view(ctx, model, args)
        else:
            assert 0, 'TODO'
        # crud_model = htypes.crud.model(
        #     value_t=pyobj_creg.actor_to_ref(self._value_t),
        #     model=mosaic.put(model),
        #     args=args,
        #     init_action_fn=self._init_action_fn_ref,
        #     commit_command_d=self._commit_command_d_ref,
        #     get_fn=mosaic.put(get_fn.piece) if get_fn else None,
        #     pick_fn=mosaic.put(pick_fn.piece) if pick_fn else None,
        #     commit_action_fn=self._commit_action_fn_ref,
        #     commit_value_field='value',
        #     )
        new_view_piece = htypes.crud.view(
            base_view=mosaic.put(base_view_piece),
            label=self._name,
            model=mosaic.put(model),
            commit_command_d=self._commit_command_d_ref,
            args=_args_dict_to_tuple(args),
            pick_fn=mosaic.put(pick_fn.piece) if pick_fn else None,
            commit_fn=self._commit_action_fn_ref,
            commit_value_field='value',
            )
        new_ctx = ctx.clone_with(
            model=new_model,
            )
        new_view = self._view_reg.animate(new_view_piece, new_ctx)
        navigator_widget = navigator_rec.widget_wr()
        if navigator_widget is None:
            raise RuntimeError("Navigator widget is gone")
        navigator_rec.view.open(ctx, new_model, new_view, navigator_widget)

    def _editor_view(self, ctx, model, args):
        if isinstance(self._value_t, TPrimitive):
            return self._primitive_view(ctx)
        else:
            return self._form_view(ctx, model, args)

    def _form_view(self, ctx, model, args):
        form_model = self._run_init(ctx, model, args)
        adapter = htypes.record_adapter.static_record_adapter(
            record_t=pyobj_creg.actor_to_ref(self._value_t),
            )
        return (form_model, htypes.form.view(mosaic.put(adapter)))

    def _primitive_view(self, ctx):
        assert 0, 'TODO'
        value = self._helpers.run_crud_init(ctx)
        if type(value) is str:
            adapter = htypes.crud.str_adapter()
            return htypes.text.edit_view(mosaic.put(adapter))
        else:
            raise NotImplementedError(f"TODO: CRUD editor: Add support for primitive type {type(value)}: {value!r}")

    def _run_init(self, ctx, model, args):
        fn = self._system_fn_creg.invite(self._init_action_fn_ref)
        fn_ctx = self._helpers.fn_ctx(ctx, model, args)
        return fn.call(fn_ctx)


class CrudHelpers:

    def __init__(self, canned_ctl_item_factory, system_fn_creg):
        self._canned_ctl_item_factory = canned_ctl_item_factory
        self._system_fn_creg = system_fn_creg

    # Override context with original elements, canned by args picker.
    def _canned_kw(self, ctx, args):
        hook = None
        kw = {}
        try:
            item_piece = args['canned_item_piece']
        except KeyError:
            pass
        else:
            item = self._canned_ctl_item_factory(item_piece, ctx)
            kw['hook'] = item.hook
            kw['widget'] = weakref.ref(item.widget)
            kw['view'] = item.view
        return kw

    def fn_ctx(self, ctx, model, args, **kw):
        if model is not None:
            model_kw = {
                'piece': model,
                'model': model,
                }
        else:
            model_kw = {}
        return ctx.clone_with(
            **model_kw,
            **args,
            **self._canned_kw(ctx, args),
            **kw,
            )


@mark.service
def crud_helpers(canned_ctl_item_factory, system_fn_creg):
    return CrudHelpers(canned_ctl_item_factory, system_fn_creg)


class CrudStrAdapter:

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx, crud_helpers):
        return cls(crud_helpers, ctx, model)

    def __init__(self, helpers, ctx, crud_model):
        self._helpers = helpers
        self._ctx = ctx 
        self._crud_model = crud_model

    @property
    def model(self):
        return self._crud_model

    def get_text(self):
        return self._helpers.run_crud_init(self._ctx, self._crud_model)


@mark.actor.model_layout_creg
def crud_model_layout(piece, lcs, ctx, system_fn_creg, visualizer, selector_reg, crud_helpers):
    if not piece.get_fn:
        assert piece.init_action_fn  # Init action fn may be omitted only for selectors.
        return _editor_view(crud_helpers, ctx, piece)
    get_fn = system_fn_creg.invite(piece.get_fn)
    if piece.init_action_fn:
        value = crud_helpers.run_crud_init(ctx, piece)
    else:
        value = None
    selector_model = get_fn.call(ctx, value=value)
    return visualizer(lcs, ctx, selector_model)


class UnboundCrudCommitCommand(UnboundCommandBase):

    def __init__(self, helpers, d, model, args, pick_fn, commit_fn, commit_value_field):
        super().__init__(d)
        self._helpers = helpers
        self._model = model
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
        return BoundCrudCommitCommand(
            self._helpers, self._d, self._model, self._args, self._pick_fn, self._commit_fn, self._commit_value_field, ctx)


class BoundCrudCommitCommand(BoundCommandBase):

    def __init__(self, helpers, d, model, args, pick_fn, commit_fn, commit_value_field, ctx):
        super().__init__(d)
        self._helpers = helpers
        self._model = model
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
        if self._pick_fn:
            value = self._pick_fn.call(self._ctx)
        else:
            value = self._pick_ctx_value(self._ctx)
        log.info("Run CRUD commit command %r: args=%s; %s=%r", self.name, self._args, self._commit_value_field, value)
        fn_ctx = self._helpers.fn_ctx(
            self._ctx, self._model, self._args,
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


@mark.ui_command_enum
def crud_commit_command_enum(view, lcs, system_fn_creg, view_reg, visualizer, crud_helpers):
    model_command = view.unbound_commit_command
    ui_command = wrap_model_command_to_ui_command(view_reg, visualizer, lcs, model_command)
    return [ui_command]
