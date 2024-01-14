from . import htypes
from .tested.code import model_command


def test_global_commands():
    commands = model_command.global_commands()
    # assert commands


def test_model_commands():
    piece = htypes.model_command_tests.sample_model()
    commands = model_command.model_commands(piece)
