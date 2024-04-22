import asyncio

from . import htypes
from .services import (
    feed_factory,
    )
from .tested.code import sample_tree


def test_sample_tree():
    piece = htypes.sample_tree.sample_tree()
    parent = htypes.sample_tree.item(100, "Some item")
    value = sample_tree.sample_tree(piece, parent)
    assert value


async def test_feed_sample_tree():
    piece = htypes.sample_tree.feed_sample_tree()
    feed = feed_factory(piece)
    parent = htypes.sample_tree.item(100, "Some item")
    value = sample_tree.feed_sample_tree(piece, parent, feed)
    assert value
    await feed.wait_for_diffs(count=1)
