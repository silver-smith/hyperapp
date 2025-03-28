from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.context import Context
from .tested.code import canned_args_command_fn


def _sample_fn(arg):
    return f'result: {arg}'


def test_command(partial_ref):
    commit_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=('arg',),
        service_params=(),
        )
    piece = htypes.command.canned_args_command_fn(
        args=(
            htypes.command.arg('arg', mosaic.put('sample-value')),
            ),
        commit_fn=mosaic.put(commit_fn),
        )
    fn = canned_args_command_fn.CannedArgsCommandFn.from_piece(piece)
    assert fn.piece == piece
    ctx = Context()
    assert not fn.missing_params(ctx)
    result = fn.call(ctx)
    assert result == 'result: sample-value'
