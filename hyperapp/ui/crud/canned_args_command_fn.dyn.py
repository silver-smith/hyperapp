from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.command_args import args_tuple_to_dict, args_dict_to_tuple


class CannedArgsCommandFn:

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece, system_fn_creg):
        args = args_tuple_to_dict(piece.args)
        return cls(
            args=args,
            commit_fn=system_fn_creg.invite(piece.commit_fn),
            )

    def __init__(self, args, commit_fn):
        self._args = args
        self._commit_fn = commit_fn

    def __repr__(self):
        return f"<CannedArgsCommandFn: {self._commit_fn}>"

    @property
    def piece(self):
        return htypes.command.canned_args_command_fn(
            args=args_dict_to_tuple(self._args),
            commit_fn=mosaic.put(self._commit_fn.piece),
            )

    def missing_params(self, ctx, **kw):
        return self._commit_fn.missing_params(ctx, **kw) - self._args.keys()

    def call(self, ctx, **kw):
        command_ctx = ctx.clone_with(
            **kw,
            **self._args,
            )
        return self._commit_fn.call(command_ctx)


@mark.actor.formatter_creg
def format_canned_arg_command_d(piece, format):
    commit_command_d = web.summon(piece.commit_command_d)
    return format(commit_command_d)
