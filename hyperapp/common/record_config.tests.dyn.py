from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .tested.code import record_config


def test_config_ctl():
    ctl_piece = htypes.record_config.config_ctl()
    ctl = record_config.RecordConfigCtl.from_piece(ctl_piece)
    assert ctl.piece == ctl_piece
