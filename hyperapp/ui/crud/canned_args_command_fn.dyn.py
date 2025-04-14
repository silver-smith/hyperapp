from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.rpc_call import DEFAULT_TIMEOUT
from .code.command_args import args_tuple_to_dict, args_dict_to_tuple


class CannedArgsCommandFn:

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece, system_fn_creg, rpc_system_call_factory):
        args = args_tuple_to_dict(piece.args)
        return cls(
            rpc_system_call_factory=rpc_system_call_factory,
            args=args,
            commit_fn=system_fn_creg.invite(piece.commit_fn),
            )

    def __init__(self, rpc_system_call_factory, args, commit_fn):
        self._rpc_system_call_factory = rpc_system_call_factory
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

    @property
    def ctx_params(self):
        return list(set(self._commit_fn.ctx_params) - self._args.keys())

    def missing_params(self, ctx, **kw):
        return self._commit_fn.missing_params(ctx, **kw) - self._args.keys()

    def call(self, ctx, **kw):
        command_ctx = ctx.clone_with(
            **kw,
            **self._args,
            )
        return self._commit_fn.call(command_ctx)

    def rpc_call(self, receiver_peer, sender_identity, ctx, timeout_sec=DEFAULT_TIMEOUT, **kw):
        rpc_call = self._rpc_system_call_factory(
            receiver_peer=receiver_peer,
            sender_identity=sender_identity,
            fn=self,
            )
        kw = {
            **ctx.as_data_dict(),
            **kw,
            }
        return rpc_call(**kw)


def _pretify_arg_value(format, value):
    title = format(value)
    # Remove possible argument prefix.
    return title.split(': ')[-1]


@mark.actor.formatter_creg
def format_canned_arg_command_d(piece, format):
    commit_command_d = web.summon(piece.commit_command_d)
    commit_command_text = format(commit_command_d)
    args = [
        _pretify_arg_value(format, web.summon(arg.value))
        for arg in piece.args
        ]
    args_str = ", ".join(args)
    return f"{commit_command_text}: {args_str}"
