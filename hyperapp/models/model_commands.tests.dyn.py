from . import htypes
from .tested.code import model_commands


def test_browse_current_model():
    model_1 = htypes.model_commands_tests.sample_model_1()
    piece_1 = model_commands.open_model_commands(model_1)
    assert piece_1
    model_2 = htypes.model_commands_tests.sample_model_2()
    piece_2 = model_commands.open_model_commands(model_2)
    assert piece_2
