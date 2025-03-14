import asyncio

from . import htypes
from .code.mark import mark
from .fixtures import feed_fixtures
from .tested.code import sample_tree


@mark.fixture
def piece():
    return htypes.sample_tree.sample_tree()


def test_sample_tree(piece):
    parent = htypes.sample_tree.item(111, "<unused>")
    value = sample_tree.sample_tree(piece, parent)
    assert value


async def test_remove_item(feed_factory, piece):
    feed = feed_factory(piece)
    current_item = htypes.sample_tree.item(111, "<unused>")
    await sample_tree.remove_tree_item(piece, current_item)
    await feed.wait_for_diffs(count=1)


async def test_append_item(feed_factory, piece):
    feed = feed_factory(piece)
    current_item = htypes.sample_tree.item(111, "<unused>")
    await sample_tree.append_tree_item(piece, current_item)
    await feed.wait_for_diffs(count=1)


async def test_insert_item(feed_factory, piece):
    feed = feed_factory(piece)
    current_item = htypes.sample_tree.item(111, "<unused>")
    await sample_tree.insert_tree_item(piece, current_item)
    await feed.wait_for_diffs(count=1)


async def test_open_sample_fn_tree():
    await sample_tree.open_sample_fn_tree()


def test_format(piece):
    title = sample_tree.format_model(piece)
    assert type(title) is str
