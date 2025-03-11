from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.data_service import DataServiceConfigCtl
from .tested.code import config_item_list


def test_item_list_model():
    piece = htypes.config_item_list.model(service_name='system')
    item_list = config_item_list.config_item_list(piece)
    assert item_list
    assert isinstance(item_list[0], htypes.config_item_list.item)


def test_open():
    piece = htypes.config_service_list.model()
    current_item = htypes.config_service_list.item(
        service_name='sample_service',
        item_count=0,  # Unused.
        )
    model = config_item_list.open_config_item_list(piece, current_item)
    assert isinstance(model, htypes.config_item_list.model)


@mark.fixture(ctl=DataServiceConfigCtl())
def sample_service(config):
    return config


@mark.fixture
def piece():
    return htypes.config_item_list.model(service_name='sample_service')


def test_open_key(piece):
    key = htypes.config_item_list_tests.sample_key(123)
    current_item = htypes.config_item_list.item(
        key=mosaic.put(key),
        key_str="<unused>",
        value_str="<unused>",
        layers=('<unused>',),
        layers_str="<unused>",
        )
    browser = config_item_list.open_config_key(piece, current_item)
    assert browser


def test_get_layer(piece):
    layer = config_item_list.config_item_get_layer(
        piece,
        layers=('source-layer',),
        )
    assert isinstance(layer, htypes.config_layer_list.layer)


def test_move(system, piece):
    key = 456

    config = {
        'sample_service': {
            key: 'value-456',
            }
        }
    source_layer = Mock(config=config)
    target_layer = Mock(config={})
    system.load_config_layer('source-layer', source_layer)
    system.load_config_layer('target-layer', target_layer)

    key_ref = mosaic.put(key)
    layers = ('source-layer',)
    value = htypes.config_layer_list.layer(
        name='target-layer',
        )
    config_item_list.config_item_move_to_another_layer(piece, key_ref, layers, value)
    source_layer.remove.assert_called_once()
    target_layer.set.assert_called_once()


def test_format_model(piece):
    title = config_item_list.format_model(piece)
    assert type(title) is str
