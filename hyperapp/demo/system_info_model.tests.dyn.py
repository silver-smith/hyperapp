from . import htypes
from .tested.code import system_info_model


def test_model():
    piece = htypes.system_info_model.model()
    info = system_info_model.system_info(piece)
    assert type(info) is list


def test_open_command():
    model = system_info_model.open_system_info()
    assert model
