from unittest.mock import Mock

from . import htypes
from .tested.services import visualizer


def make_lcs():
    lcs = Mock()
    # Fall thru to default layout.
    lcs.get.return_value = None
    return lcs


def test_string():
    lcs = make_lcs()
    layout = visualizer(lcs, "Sample text")
    assert layout


def test_int():
    lcs = make_lcs()
    layout = visualizer(lcs, 12345)
    assert layout


def test_list():
    value = (
        htypes.list_tests.item(1, "First"),
        htypes.list_tests.item(2, "Second"),
        )
    lcs = make_lcs()
    layout = visualizer(lcs, value)
    assert layout


def test_sample_list():
    piece = htypes.sample_list.sample_list()
    lcs = make_lcs()
    layout = visualizer(lcs, piece)
    assert layout


def test_sample_tree():
    piece = htypes.sample_tree.sample_tree()
    lcs = make_lcs()
    layout = visualizer(lcs, piece)
    assert layout


def test_sample_record():
    piece = htypes.sample_record.sample_record()
    lcs = make_lcs()
    layout = visualizer(lcs, piece)
    assert layout
