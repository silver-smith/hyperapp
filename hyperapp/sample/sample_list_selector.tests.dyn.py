from . import htypes
from .tested.code import sample_list_selector


def test_get():
    value = htypes.sample_list_selector.item(123)  # Unused.
    model = sample_list_selector.sample_list_get(value)
    assert model


def test_pick():
    piece = htypes.sample_list.sample_list()  # Unused.
    current_item = htypes.sample_list.item(
        id=123,
        title="<unused>",
        desc="<unused>",
        )
    value = sample_list_selector.sample_list_pick(piece, current_item)
    assert value == htypes.sample_list_selector.item(123)
    
