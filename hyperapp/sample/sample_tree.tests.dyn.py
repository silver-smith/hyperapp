import asyncio

from . import htypes
from .fixtures import feed_fixtures
from .tested.code import sample_tree


async def test_remove_item():
    piece = htypes.sample_tree.sample_tree()
    current_item = htypes.sample_tree.item(100, "<unused>")
    await sample_tree.remove_tree_item(piece, current_item)


async def test_open_sample_fn_tree():
    await sample_tree.open_sample_fn_tree()


async def test_open_feed_sample_fn_tree():
    await sample_tree.open_feed_sample_fn_tree()


def test_sample_tree():
    piece = htypes.sample_tree.sample_tree()
    parent = htypes.sample_tree.item(100, "Some item")
    value = sample_tree.sample_tree(piece, parent)
    assert value


async def test_feed_sample_tree(feed_factory):
    piece = htypes.sample_tree.feed_sample_tree()
    feed = feed_factory(piece)
    parent = htypes.sample_tree.item(100, "Some item")
    value = sample_tree.feed_sample_tree(piece, parent, feed)
    assert value
    await feed.wait_for_diffs(count=1)
