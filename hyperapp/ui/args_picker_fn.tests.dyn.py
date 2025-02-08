from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .tested.code import args_picker_fn

def _sample_commit(sample_value):
    pass


def test_args_picker_fn():
    commit_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_commit),
        ctx_params=('sample_value',),
        service_params=(),
        )
    piece = htypes.command.args_picker_command_fn(
        name='sample-fn',
        args=(
            htypes.command.arg(
                name='sample_value',
                t=pyobj_creg.actor_to_ref(htypes.args_picker_fn_tests.sample_value),
                ),
            ),
        commit_command_d=mosaic.put(htypes.args_picker_fn_tests.sample_commit_command_d()),
        commit_fn=mosaic.put(commit_fn),
        )
    picker_fn = args_picker_fn.ArgsPickerFn.from_piece(piece)
