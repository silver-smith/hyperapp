from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark


class ArgsPickerFn:

    _required_kw = {'navigator', 'hook'}

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece, crud, system_fn_creg, editor_default_reg):
        args = {
            arg.name: pyobj_creg.invite(arg.t)
            for arg in piece.args
            }
        return cls(
            system_fn_creg=system_fn_creg,
            crud=crud,
            editor_default_reg=editor_default_reg,
            name=piece.name,
            args=args,
            commit_command_d=web.summon(piece.commit_command_d),
            commit_fn_ref=piece.commit_fn,
            )

    def __init__(self, system_fn_creg, crud, editor_default_reg, name, args, commit_command_d, commit_fn_ref):
        self._system_fn_creg = system_fn_creg
        self._crud = crud
        self._editor_default_reg = editor_default_reg
        self._name = name
        self._args = args
        self._commit_command_d = commit_command_d
        self._commit_fn_ref = commit_fn_ref

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
        return args

    def call(self, ctx, **kw):
        ctx_kw = {**ctx.as_dict(), **kw}
        return self._open(
            navigator_rec=ctx_kw['navigator'],
            ctx=ctx,
            )

    def _open(self, navigator_rec, ctx):
        assert len(self._args) == 1, "TODO: Pick args from context and implement multi-args editor"
        [(value_field, value_t)] = self._args.items()
        try:
            get_default_fn = self._editor_default_reg[value_t]
        except KeyError:
            get_default_fn = None
        commit_args = self._can_crud_args(ctx)
        return self._crud.open_view(
            navigator_rec=navigator_rec,
            ctx=ctx,
            value_t=value_t,
            label=f"Input: {value_field}",
            init_action_fn=self._system_fn_creg.animate(get_default_fn),
            commit_command_d_ref=mosaic.put(self._commit_command_d),
            commit_action_fn_ref=self._commit_fn_ref,
            commit_value_field=value_field,
            model=None,
            commit_args=commit_args,
            )
