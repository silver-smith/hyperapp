from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark


class ArgsPickerFn:

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece, editor_default_reg, selector_reg):
        args = {
            arg.name: pyobj_creg.invite(arg.t)
            for arg in piece.args
            }
        return cls(
            editor_default_reg=editor_default_reg,
            selector_reg=selector_reg,
            name=piece.name,
            args=args,
            commit_command_d=web.summon(piece.commit_command_d),
            commit_fn_ref=piece.commit_fn,
            )

    def __init__(self, editor_default_reg, selector_reg, name, args, commit_command_d, commit_fn_ref):
        self._editor_default_reg = editor_default_reg
        self._selector_reg = selector_reg
        self._name = name
        self._args = args
        self._commit_command_d = commit_command_d
        self._commit_fn_ref = commit_fn_ref

    def __repr__(self):
        return f"<ArgsPickerFn {self._name}: {self._args}>"

    def missing_params(self, ctx, **kw):
        return set()
        # ctx_kw = {**ctx.as_dict(), **kw}
        # return self._required_kw - ctx_kw.keys()

    def call(self, ctx, **kw):
        ctx_kw = {**ctx.as_dict(), **kw}
        assert len(self._args) == 1, "TODO: Pick args from context and implement multi-args editor"
        [(value_field, value_t)] = self._args.items()
        get_default_fn = self._editor_default_reg[value_t]
        assert 0, get_default_fn
        try:
            selector = self._selector_reg[value_t]
        except KeyError:
            get_fn = None
            pick_fn = None
        else:
            get_fn = selector.get_fn
            pick_fn = selector.pick_fn
        return htypes.crud.model(
            value_t=pyobj_creg.actor_to_ref(value_t),
            model=None,
            args=(),
            init_action_fn=self._init_action_fn_ref,
            commit_command_d=mosaic.put(self._commit_command_d),
            get_fn=mosaic.put(get_fn.piece) if get_fn is not None else None,
            pick_fn=mosaic.put(pick_fn.piece) if pick_fn is not None else None,
            commit_action_fn=self._commit_fn_ref,
            commit_value_field=value_field,
            )
