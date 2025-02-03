from unittest.mock import Mock

from . import htypes
from .code.mark import mark
from .tested.code import config_item_list


@mark.fixture
def piece():
    return htypes.config_item_list.model(service_name='system')


def test_item_list_model(piece):
    item_list = config_item_list.config_item_list(piece)
    assert item_list
    assert isinstance(item_list[0], htypes.config_item_list.item)


def test_open():
    piece = htypes.config_service_list.model()
    current_item = htypes.config_service_list.item(
        service_name='system',
        item_count=0,  # Unused.
        )
    model = config_item_list.open_config_item_list(piece, current_item)
    assert isinstance(model, htypes.config_item_list.model)


def test_get_layer(piece):
    layer = config_item_list.config_item_get_layer(
        piece,
        layers=('source-layer',),
        )
    assert isinstance(layer, htypes.config_layer_list.layer)


def test_move(system, piece):
    source_layer = Mock(config={})
    target_layer = Mock(config={})
    system.load_config_layer('source-layer', source_layer)
    system.load_config_layer('target-layer', target_layer)

    key = 123
    layers = ('source-layer',)
    value = htypes.config_layer_list.layer(
        name='target-layer',
        )
    config_item_list.config_item_move_to_another_layer(piece, key, layers, value)
    source_layer.remove.assert_called_once()
    target_layer.set.assert_called_once()
