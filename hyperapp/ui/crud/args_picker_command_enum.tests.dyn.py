from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.context import Context
from .code.model_command import UnboundModelCommand
from .code.ui_command import UnboundUiCommand
from .code.arg_mark import value_mark_name
from .tested.code import args_picker_command_enum


def _sample_fn():
    pass


@mark.fixture
def ctx():
    return Context()


@mark.fixture
def canned_ctx():
    return Context({value_mark_name(htypes.builtin.string): "Sample value"})


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
        required_args=(
            htypes.command.arg_t(
                name='name',
                t=pyobj_creg.actor_to_ref(htypes.builtin.string),
                ),
            ),
        args_picker_command_d=mosaic.put(d),
        commit_command_d=mosaic.put(d),
        commit_fn=mosaic.put(fn),
        )


def test_model_args_picker(ctx, args_picker_enum):
    piece = args_picker_enum(htypes.command.model_args_picker_command_enumerator)
    enum = args_picker_command_enum.UnboundArgsPickerModelCommandEnumerator.from_piece(piece)
    assert isinstance(enum, args_picker_command_enum.UnboundArgsPickerModelCommandEnumerator)
    command_list = enum.enum_commands(ctx)
    assert type(command_list) is list
    [command] = command_list
    assert isinstance(command, UnboundModelCommand)
    assert isinstance(web.summon(command.piece.system_fn), htypes.command.args_picker_command_fn)


def test_ui_args_picker(ctx, args_picker_enum):
    piece = args_picker_enum(htypes.command.ui_args_picker_command_enumerator)
    enum = args_picker_command_enum.UnboundArgsPickerUiCommandEnumerator.from_piece(piece)
    assert isinstance(enum, args_picker_command_enum.UnboundArgsPickerUiCommandEnumerator)
    command_list = enum.enum_commands(ctx)
    assert type(command_list) is list
    [command] = command_list
    assert isinstance(command, UnboundUiCommand)
    assert isinstance(web.summon(command.piece.system_fn), htypes.command.args_picker_command_fn)


def test_model_canned(canned_ctx, args_picker_enum):
    piece = args_picker_enum(htypes.command.model_args_picker_command_enumerator)
    enum = args_picker_command_enum.UnboundArgsPickerModelCommandEnumerator.from_piece(piece)
    assert isinstance(enum, args_picker_command_enum.UnboundArgsPickerModelCommandEnumerator)
    command_list = enum.enum_commands(canned_ctx)
    assert type(command_list) is list
    [command] = command_list
    assert isinstance(command, UnboundModelCommand)
    assert isinstance(web.summon(command.piece.system_fn), htypes.command.canned_args_command_fn)


def test_ui_canned(canned_ctx, args_picker_enum):
    piece = args_picker_enum(htypes.command.ui_args_picker_command_enumerator)
    enum = args_picker_command_enum.UnboundArgsPickerUiCommandEnumerator.from_piece(piece)
    assert isinstance(enum, args_picker_command_enum.UnboundArgsPickerUiCommandEnumerator)
    command_list = enum.enum_commands(canned_ctx)
    assert type(command_list) is list
    [command] = command_list
    assert isinstance(command, UnboundUiCommand)
    assert isinstance(web.summon(command.piece.system_fn), htypes.command.canned_args_command_fn)
