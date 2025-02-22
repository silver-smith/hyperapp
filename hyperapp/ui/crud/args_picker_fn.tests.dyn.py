from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import args_picker_fn


def _editor_default():
    return 123


def _sample_commit(sample_value):
    pass


@mark.config_fixture('editor_default_reg')
def editor_default_reg_config():
    fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_editor_default),
        ctx_params=(),
        service_params=(),
        )
    return {htypes.args_picker_fn_tests.sample_value: fn}


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
    ctx = Context(
        hook=Mock(canned_item_piece=None),
        model=None,
        model_state=None,
        )
    picker_fn.call(ctx)
