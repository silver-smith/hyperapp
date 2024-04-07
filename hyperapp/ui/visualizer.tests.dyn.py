from . import htypes
from .tested.code import visualizer
from .tested.services import visualizer


def test_text():
    layout = visualizer("Sample text")
    assert layout


def test_list():
    value = (
        htypes.list_tests.item(1, "First"),
        htypes.list_tests.item(2, "Second"),
        )
    layout = visualizer(value)
    assert layout


def test_sample_list():
    piece = htypes.sample_list.sample_list()
    layout = visualizer(piece)
    assert layout


def test_sample_tree():
    piece = htypes.sample_tree.sample_tree()
    layout = visualizer(piece)
    assert layout
