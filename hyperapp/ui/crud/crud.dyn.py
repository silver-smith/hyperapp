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
from .code.record_adapter import FnRecordAdapterBase
from .code.construct_default_form import construct_default_form

log = logging.getLogger(__name__)


def _args_dict_to_tuple(args):
    if args is None:
        return ()
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
    def from_piece(cls, piece, ctx, system_fn_creg, view_reg, crud):
        base_view = view_reg.invite(piece.base_view, ctx)
        model = web.summon_opt(piece.model)
        command_d = web.summon(piece.commit_command_d)
        return cls(
            system_fn_creg, crud, base_view, piece.label, model,
            command_d, _args_tuple_to_dict(piece.args), piece.pick_fn, piece.commit_fn, piece.commit_value_field)

    def __init__(
            self, system_fn_creg, crud, base_view, label, model,
            command_d, args, pick_fn_ref, commit_fn_ref, commit_value_field):
        super().__init__(base_view, label)
        self._system_fn_creg = system_fn_creg
        self._crud = crud
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
            self._crud, self._command_d, self._model, self._args, pick_fn, commit_fn, self._commit_value_field)


class CrudOpenFn:

    _required_kw = {'navigator', 'model', 'current_item'}

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece, system_fn_creg, crud):
        return cls(
            crud=crud,
            name=piece.name,
            value_t=pyobj_creg.invite(piece.value_t),
            key_fields=piece.key_fields,
            init_action_fn=system_fn_creg.invite(piece.init_action_fn),
            commit_command_d_ref=piece.commit_command_d,
            commit_action_fn_ref=piece.commit_action_fn,
            )

    def __init__(self, crud, name, value_t, key_fields, init_action_fn, commit_command_d_ref, commit_action_fn_ref):
        self._crud = crud
        self._name = name
        self._value_t = value_t
        self._key_fields = key_fields
        self._init_action_fn = init_action_fn
        self._commit_command_d_ref = commit_command_d_ref
        self._commit_action_fn_ref = commit_action_fn_ref

    def __repr__(self):
        return f"<CrudOpenFn {self._name} keys={self._key_fields}>"

    def missing_params(self, ctx, **kw):
        ctx_kw = {**ctx.as_dict(), **kw}
        return self._required_kw - ctx_kw.keys()

    def call(self, ctx, **kw):
        ctx_kw = {**ctx.as_dict(), **kw}
        return self._open(
            navigator_rec=ctx_kw['navigator'],
            model=ctx_kw['model'],
            current_item=ctx_kw['current_item'],
            ctx=ctx,
            )

    def _open(self, navigator_rec, model, current_item, ctx):
        args = {
            name: getattr(current_item, name)
            for name in self._key_fields
            }
        self._crud.open_view(
            navigator_rec=navigator_rec,
            ctx=ctx,
            value_t=self._value_t,
            label=self._name,
            init_action_fn=self._init_action_fn,
            commit_command_d_ref=self._commit_command_d_ref,
            commit_action_fn_ref=self._commit_action_fn_ref,
            commit_value_field='value',
            model=model,
            init_args=args,
            commit_args=args,
            )


class CrudRecordAdapter(FnRecordAdapterBase):

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx, system_fn_creg, feed_factory, crud):
        record_t = pyobj_creg.invite(piece.record_t)
        value = cls._get_edit_value(model, record_t)
        init_fn = system_fn_creg.invite(piece.init_fn)
        args = _args_tuple_to_dict(piece.args)
        return cls(feed_factory, model, record_t, ctx, value, crud, init_fn, args)

    def __init__(self, feed_factory, model, record_t, ctx, value, crud, init_fn, args):
        super().__init__(feed_factory, model, record_t, ctx, value)
        self._crud = crud
        self._args = args
        self._init_fn = init_fn

    def _get_value(self):
        fn_ctx = self._crud.fn_ctx(self._ctx, self._model, self._args)
        return self._init_fn.call(fn_ctx)


class Crud:

    def __init__(self, canned_ctl_item_factory, system_fn_creg, visualizer, view_reg, selector_reg):
        self._canned_ctl_item_factory = canned_ctl_item_factory
        self._system_fn_creg = system_fn_creg
        self._visualizer = visualizer
        self._view_reg = view_reg
        self._selector_reg = selector_reg

    def fn_ctx(self, ctx, model, args, **kw):
        if args is None:
            args = {}
        if model is not None:
            model_layout_kw = {
                'piece': model,
                'model': model,
                }
        else:
            model_layout_kw = {}
        return ctx.clone_with(
            **model_layout_kw,
            **args,
            **self._canned_kw(ctx, args),
            **kw,
            )

    def open_view(
            self,
            navigator_rec,
            ctx,
            value_t,
            label,
            init_action_fn,
            commit_command_d_ref,
            commit_action_fn_ref,
            commit_value_field,
            model,
            init_args=None,
            commit_args=None,
            ):
        try:
            selector = self._selector_reg[value_t]
        except KeyError:
            get_fn = None
            pick_fn = None
        else:
            get_fn = selector.get_fn
            pick_fn = selector.pick_fn
        if not get_fn:
            # assert init_action_fn  # Init action fn may be omitted only for selectors.
            if isinstance(value_t, TPrimitive):
                base_view_piece = self._primitive_view(value_t)
                new_model = self._run_init(ctx, init_action_fn, model, init_args)
            else:
                base_view_piece = self._form_view(value_t, init_action_fn, init_args)
                new_model = htypes.crud.form_model()
        else:
            new_model = self._run_init(ctx, init_action_fn, model, init_args)
            base_view_piece = self._selector_view(ctx, get_fn, new_model)
        new_view_piece = htypes.crud.view(
            base_view=mosaic.put(base_view_piece),
            label=label,
            model=mosaic.put(model),
            commit_command_d=commit_command_d_ref,
            args=_args_dict_to_tuple(commit_args),
            pick_fn=mosaic.put(pick_fn.piece) if pick_fn else None,
            commit_fn=commit_action_fn_ref,
            commit_value_field=commit_value_field,
            )
        new_ctx = ctx.clone_with(
            model=new_model,
            )
        new_view = self._view_reg.animate(new_view_piece, new_ctx)
        navigator_widget = navigator_rec.widget_wr()
        if navigator_widget is None:
            raise RuntimeError("Navigator widget is gone")
        layout_k = htypes.crud.layout_k(
            commit_command_d=commit_command_d_ref,
            )
        navigator_rec.view.open(ctx, new_model, new_view, navigator_widget, layout_k=layout_k)

    # Override context with original elements, canned by args picker.
    def _canned_kw(self, ctx, args):
        kw = {}
        try:
            item_piece = args['canned_item_piece']
        except KeyError:
            pass
        else:
            item = self._canned_ctl_item_factory(item_piece, ctx)
            if item:  # None if view&widget are already gone.
                kw['hook'] = item.hook
                kw['widget'] = weakref.ref(item.widget)
                kw['view'] = item.view
        return kw

    def _form_view(self, value_t, init_action_fn, init_args):
        adapter = htypes.crud.record_adapter(
            record_t=pyobj_creg.actor_to_ref(value_t),
            init_fn=mosaic.put(init_action_fn.piece),
            args=_args_dict_to_tuple(init_args),
            )
        return construct_default_form(adapter, value_t)

    def _primitive_view(self, value_t):
        if value_t is htypes.builtin.string:
            adapter = htypes.str_adapter.static_str_adapter()
            return htypes.text.edit_view(mosaic.put(adapter))
        raise NotImplementedError(f"TODO: CRUD editor: Add support for primitive type: {value_t}")

    def _selector_view(self, ctx, get_fn, value):
        selector_model = get_fn.call(ctx, value=value)
        selector_model_t = deduce_t(selector_model)
        return self._visualizer(ctx, selector_model_t)

    def _run_init(self, ctx, init_action_fn, model, args):
        fn_ctx = self.fn_ctx(ctx, model, args)
        return init_action_fn.call(fn_ctx)


@mark.service
def crud(canned_ctl_item_factory, system_fn_creg, visualizer, view_reg, selector_reg):
    return Crud(canned_ctl_item_factory, system_fn_creg, visualizer, view_reg, selector_reg)


class UnboundCrudCommitCommand(UnboundCommandBase):

    def __init__(self, crud, d, model, args, pick_fn, commit_fn, commit_value_field):
        super().__init__(d)
        self._crud = crud
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
            self._crud, self._d, self.properties, self._model, self._args, self._pick_fn, self._commit_fn, self._commit_value_field, ctx)


class BoundCrudCommitCommand(BoundCommandBase):

    def __init__(self, crud, d, properties, model, args, pick_fn, commit_fn, commit_value_field, ctx):
        super().__init__(d, ctx)
        self._crud = crud
        self._properties = properties
        self._model = model
        self._args = args
        self._pick_fn = pick_fn
        self._commit_fn = commit_fn
        self._commit_value_field = commit_value_field

    @property
    def enabled(self):
        return not self._missing_params

    @property
    def disabled_reason(self):
        params = ", ".join(self._missing_params)
        return f"Params not ready: {params}"

    @property
    def properties(self):
        return self._properties

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
        fn_ctx = self._crud.fn_ctx(
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
def crud_commit_command_enum(view, lcs, system_fn_creg, view_reg, visualizer):
    model_command = view.unbound_commit_command
    ui_command = wrap_model_command_to_ui_command(view_reg, visualizer, lcs, model_command)
    return [ui_command]
