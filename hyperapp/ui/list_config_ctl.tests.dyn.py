from . import htypes
from .tested.code import list_config_ctl


def test_typed_ctl():
    piece = htypes.list_config_ctl.dict_list_config_ctl()
    ctl = list_config_ctl.DictListConfigCtl.from_piece(piece)
    assert ctl.piece == piece
