from . import htypes
from .services import (
    mosaic,
    )
from .tested.code import list_config_ctl


def test_typed_ctl(config_ctl_creg):
    key_ctl = htypes.system.one_way_key_ctl()
    value_ctl = htypes.system.actor_value_ctl()
    piece = htypes.list_config_ctl.dict_list_config_ctl(
        key_ctl=mosaic.put(key_ctl),
        value_ctl=mosaic.put(value_ctl),
        )
    ctl = config_ctl_creg.animate(piece)
    assert ctl.piece == piece
