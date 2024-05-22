from unittest.mock import Mock

from . import htypes
from .services import (
    fn_to_ref,
    mosaic,
    )
from .code.context import Context
from .tested.code import model_command
from .tested.services import (
    enum_model_commands,
    global_commands,
    model_commands,
    )


def test_global_commands():
    commands = global_commands()
    # assert commands


def test_model_commands():
    piece = htypes.model_command_tests.sample_model()
    commands = model_commands(piece)


def test_enum_model_commands():
    ctx = Context()
    piece = htypes.model_command_tests.sample_model()
    commands = list(enum_model_commands(piece, ctx))


def _sample_fn():
    return 123


def test_model_command_ctr():
    piece = htypes.ui.model_command_impl(
        function=fn_to_ref(_sample_fn),
        params=(),
        )
    ctx = Context()
    command = model_command.model_command_impl_from_piece(piece, ctx)
    assert isinstance(command, model_command.ModelCommandImpl)
