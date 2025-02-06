from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .tested.code import typed_cfg_item


def _sample_fn(view, state, sample_service):
    return f'sample-fn: {state}, {sample_service}'


@mark.fixture.obj
def value():
    return htypes.typed_cfg_item_tests.value()


@mark.fixture.obj
def piece(value):
    return htypes.cfg_item.typed_cfg_item(
        t=pyobj_creg.actor_to_ref(htypes.typed_cfg_item_tests.key),
        value=mosaic.put(value),
        )


def test_construct(piece):
    cfg_item = typed_cfg_item.TypedCfgItem.from_piece(piece)
    assert cfg_item.piece == piece


def test_resolve(system, value, piece):
    cfg_item = typed_cfg_item.TypedCfgItem.from_piece(piece)
    resolved_value = cfg_item.resolve(system, '<unused>')
    assert resolved_value == value
