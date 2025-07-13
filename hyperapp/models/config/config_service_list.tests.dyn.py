from unittest.mock import Mock, MagicMock

from . import htypes
from .code.mark import mark
from .code.data_service import DataServiceConfigCtl
from .fixtures import feed_fixtures
from .tested.code import config_service_list


@mark.fixture
def piece():
    return htypes.config_service_list.model(
        layer=None,
        )


def test_service_list_model(piece):
    item_list = config_service_list.config_service_list(piece)
    assert item_list
    assert isinstance(item_list[0], htypes.config_service_list.item)


def test_service_layer_list_model(system):
    piece = htypes.config_service_list.model(
        layer=system.default_layer_name,
        )
    item_list = config_service_list.config_service_list(piece)
    # Item list may be empty for default RC layer.


def test_open():
    model = config_service_list.open_config_service_list()
    assert isinstance(model, htypes.config_service_list.model)


@mark.fixture.obj(ctl=DataServiceConfigCtl())
def assoc_key():
    reg = MagicMock()
    reg.get.return_value = None
    return reg


async def test_toggle_assoc(assoc_key, piece):
    current_key = 'assoc_key'
    await config_service_list.toggle_assoc(piece, current_key)
    assoc_key.__setitem__.assert_called_once()
    assoc_key.__contains__.return_value = True
    await config_service_list.toggle_assoc(piece, current_key)
    assoc_key.__delitem__.assert_called_once()


def test_format_model(piece):
    title = config_service_list.format_model(piece)
    assert type(title) is str
