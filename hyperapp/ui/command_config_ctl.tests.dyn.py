from . import htypes
from .tested.code import command_config_ctl


def test_typed_ctl():
    piece = htypes.command.typed_config_ctl()
    ctl = command_config_ctl.TypedCommandConfigCtl.from_piece(piece)
    assert ctl.piece == piece


def test_untyped_ctl():
    piece = htypes.command.untyped_config_ctl()
    ctl = command_config_ctl.UntypedCommandConfigCtl.from_piece(piece)
    assert ctl.piece == piece
