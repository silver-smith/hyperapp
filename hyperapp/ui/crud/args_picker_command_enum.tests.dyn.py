from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import args_picker_command_enum


def _sample_fn():
    pass


@mark.fixture
def args_picker_enum(enum_t):
    d = htypes.args_picker_command_enum_tests.sample_command_d()
    fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_sample_fn),
        ctx_params=(),
        service_params=(),
        )
    return enum_t(
        name='sample-command',
        is_global=False,
        args=(),
        args_picker_command_d=mosaic.put(d),
        commit_command_d=mosaic.put(d),
        commit_fn=mosaic.put(fn),
        )


def test_model_args_picker_enumerator_from_piece(args_picker_enum):
    piece = args_picker_enum(htypes.command.model_args_picker_command_enumerator)
    enum = args_picker_command_enum.UnboundArgsPickerCommandEnumerator.from_piece(piece)
    assert isinstance(enum, args_picker_command_enum.UnboundArgsPickerCommandEnumerator)


def test_ui_args_picker_enumerator_from_piece(args_picker_enum):
    piece = args_picker_enum(htypes.command.ui_args_picker_command_enumerator)
    enum = args_picker_command_enum.UnboundArgsPickerCommandEnumerator.from_piece(piece)
    assert isinstance(enum, args_picker_command_enum.UnboundArgsPickerCommandEnumerator)
