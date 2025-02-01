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
