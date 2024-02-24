import asyncio

from . import htypes
from .code.list_diff import ListDiff
from .tested.code import sample_list


def test_sample_list():
    value = sample_list.sample_list(htypes.sample_list.sample_list())
    assert value


class MockFeed:

    def __init__(self, queue):
        self._queue = queue

    def send(self, diff):
        self._queue.put_nowait(diff)


async def test_feed_sample_list():
    queue = asyncio.Queue()
    feed = MockFeed(queue)
    value = sample_list.feed_sample_list(htypes.sample_list.feed_sample_list(), feed)
    assert value
    diff = await queue.get()
    assert isinstance(diff, ListDiff.Append), repr(diff)
