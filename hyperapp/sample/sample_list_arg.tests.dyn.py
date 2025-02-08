from . import htypes
from .tested.code import sample_list_arg


def test_default():
    item = sample_list_arg.sample_list_default()
    assert item


def test_show_sample_list_item():
    item = htypes.sample_list_selector.item(id=123)
    text = sample_list_arg.show_sample_list_item(item)
    assert type(text) is str
