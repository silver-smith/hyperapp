from . import htypes
from .tested.code import list_config_ctl


def test_typed_ctl(config_ctl_creg):
    piece = htypes.list_config_ctl.dict_list_config_ctl()
    ctl = config_ctl_creg.animate(piece)
    assert ctl.piece == piece
