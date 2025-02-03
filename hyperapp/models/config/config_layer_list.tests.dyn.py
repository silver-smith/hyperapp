from . import htypes
from .code.mark import mark
from .tested.code import config_layer_list


@mark.fixture
def piece():
    return htypes.config_layer_list.model()


def test_layer_list_model(piece):
    item_list = config_layer_list.config_layer_list(piece)
    assert item_list
    assert isinstance(item_list[0], htypes.config_layer_list.item)


def test_open():
    model = config_layer_list.open_config_layer_list()
    assert isinstance(model, htypes.config_layer_list.model)


def test_selector_get():
    # value is actually unused.
    value = htypes.config_layer_list.layer(
        name='sample-layer',
        )
    piece = config_layer_list.layer_get(value)
    assert isinstance(piece, htypes.config_layer_list.model)


def test_selector_put():
    piece = htypes.config_layer_list.model()  # Unused.
    current_item = htypes.config_layer_list.item(
        name='sample-layer',
        service_count=0,  # Unused.
        )
    value = config_layer_list.layer_put(piece, current_item)
    assert value == htypes.config_layer_list.layer('sample-layer')
