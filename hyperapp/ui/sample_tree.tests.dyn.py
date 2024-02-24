import asyncio

from . import htypes
# from .code.tree_diff import TreeDiff
from .tested.code import sample_tree


def test_sample_tree():
    piece = htypes.sample_tree.sample_tree()
    parent = htypes.sample_tree.item(100, "Some item")
    value = sample_tree.sample_tree(piece, parent)
    assert value


class MockFeed:

    def __init__(self, queue):
        self._queue = queue

    def send(self, diff):
        self._queue.put_nowait(diff)


async def test_feed_sample_tree():
    queue = asyncio.Queue()
    feed = MockFeed(queue)
    piece = htypes.sample_tree.feed_sample_tree()
    parent = htypes.sample_tree.item(100, "Some item")
    value = sample_tree.feed_sample_tree(piece, parent, feed)
    assert value
    diff = await queue.get()
    # assert isinstance(diff, TreeDiff.Append), repr(diff)
