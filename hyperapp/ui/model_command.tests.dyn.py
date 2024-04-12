from unittest.mock import Mock

from . import htypes
from .services import (
    data_to_res,
    fn_to_res,
    mosaic,
    )
from .tested.code import model_command


def test_global_commands():
    commands = model_command.global_commands()
    # assert commands


def test_model_commands():
    piece = htypes.model_command_tests.sample_model()
    commands = model_command.model_commands(piece)


def test_enum_model_commands():
    piece = htypes.model_command_tests.sample_model()
    commands = list(model_command.enum_model_commands(piece, model_state=None))


def _sample_fn():
    return 123


def test_model_command_ctr():
    command_d_res = data_to_res(htypes.model_command_tests.sample_command_d())
    fn_res = fn_to_res(_sample_fn)
    piece = htypes.ui.model_command(
        d=mosaic.put(command_d_res),
        name='sample_command',
        function=mosaic.put(fn_res),
        params=(),
        )
    command = model_command.model_command_from_piece(
        piece, view=None, model_piece=None, widget=Mock(), wrappers=[])
    assert isinstance(command, model_command.ModelCommand)
