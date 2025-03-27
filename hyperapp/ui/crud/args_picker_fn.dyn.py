import inspect

from hyperapp.boot.htypes.deduce_value_type import DeduceTypeError

from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.arg_mark import value_mark_name


def args_dict_to_tuple(args):
    return tuple(
        htypes.command.arg(
            name=name,
            t=pyobj_creg.actor_to_ref(arg.t),
            )
        for name, value in args.items()
        )


def args_tuple_to_dict(args):
    return {
        arg.name: pyobj_creg.invite(arg.t)
        for arg in args
        }


class ArgsPickerFn:

    _required_kw = {'navigator', 'hook'}

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece, crud, system_fn_creg, editor_default_reg):
        args = args_tuple_to_dict(piece.args)
        return cls(
            system_fn_creg=system_fn_creg,
            crud=crud,
            editor_default_reg=editor_default_reg,
            name=piece.name,
            args=args,
            commit_command_d=web.summon(piece.commit_command_d),
            commit_fn=system_fn_creg.invite(piece.commit_fn),
            )

    def __init__(self, system_fn_creg, crud, editor_default_reg, name, args, commit_command_d, commit_fn):
        self._system_fn_creg = system_fn_creg
        self._crud = crud
        self._editor_default_reg = editor_default_reg
        self._name = name
        self._args = args
        self._commit_command_d = commit_command_d
        self._commit_fn = commit_fn

    def __repr__(self):
        return f"<ArgsPickerFn {self._name}: {self._args}>"

    def missing_params(self, ctx, **kw):
        ctx_kw = {**ctx.as_dict(), **kw}
        return self._required_kw - ctx_kw.keys()

    @staticmethod
    def _can_crud_args(ctx):
        args = {}
        args['canned_item_piece'] = ctx.hook.canned_item_piece
        if 'model' in ctx:
            args['model'] = ctx.model
        if 'model_state' in ctx:
            args['model_state'] = ctx.model_state
        if 'element_idx' in ctx:
            args['element_idx'] = ctx.element_idx
        return args

    def call(self, ctx, **kw):
        ctx_kw = {**ctx.as_dict(), **kw}
        return self._open(
            navigator_rec=ctx_kw['navigator'],
            ctx=ctx,
            )

    def _open(self, navigator_rec, ctx):
        args, required_args = self._pick_args_from_context(ctx)
        if len(required_args) > 1:
            required_str = ', '.join(name for name, t in required_args.items())
            raise RuntimeError(f"More than 1 args to pick is not supported: {required_str}")
        if not required_args:
            return self._run_commit_fn(ctx, args)
        [(value_field, value_t)] = required_args.items()
        try:
            get_default_fn = self._editor_default_reg[value_t]
        except KeyError:
            get_default_fn = None
        commit_args = self._can_crud_args(ctx)
        return self._crud.open_view(
            navigator_rec=navigator_rec,
            ctx=ctx,
            value_t=value_t,
            label=f"{value_field} for: {self._name}",
            init_action_fn=self._system_fn_creg.animate_opt(get_default_fn),
            commit_command_d=self._commit_command_d,
            commit_action_fn_ref=mosaic.put(self._commit_fn.piece),
            commit_value_field=value_field,
            model=commit_args.get('model'),
            commit_args=commit_args,
            )

    def _pick_args_from_context(self, ctx):
        args = {}
        required_args = {}
        for name, t in self._args.items():
            value = self._pick_arg(ctx, name, t)
            if value is None:
                required_args[name] = t
            else:
                args[name] = value
        return (args, required_args)

    def _pick_arg(self, ctx, name, required_t):
        ctx_name = value_mark_name(required_t)
        try:
            value = ctx[ctx_name]
        except KeyError:
            return None
        try:
            value_t = deduce_t(value)
        except DeduceTypeError:
            return None
        if required_t is value_t:
            return value
        return None

    async def _run_commit_fn(self, ctx, args):
        fn_ctx = ctx.clone_with(args)
        result = self._commit_fn.call(fn_ctx)
        if inspect.iscoroutine(result):
            result = await result
        return result
