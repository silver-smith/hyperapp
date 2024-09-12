from . import htypes
from .tested.code import command_config_ctl


def test_ctl():
    piece = htypes.command.config_ctl()
    ctl = command_config_ctl.CommandConfigCtl.from_piece(piece)
    assert ctl.piece == piece
    config = ctl.items_to_data([])
    assert not config.items
