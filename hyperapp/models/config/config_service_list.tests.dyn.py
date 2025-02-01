from . import htypes
from .code.mark import mark
from .tested.code import config_service_list


@mark.fixture
def piece():
    return htypes.config_service_list.model()


def test_service_list_model(piece):
    item_list = config_service_list.config_service_list(piece)
    assert item_list
    assert isinstance(item_list[0], htypes.config_service_list.item)


def test_open():
    model = config_service_list.open_config_service_list()
    assert isinstance(model, htypes.config_service_list.model)
