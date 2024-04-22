import asyncio

from . import htypes
from .services import (
    feed_factory,
    )
from .code.list_diff import ListDiff
from .tested.code import sample_list


def test_sample_list():
    value = sample_list.sample_list(htypes.sample_list.sample_list())
    assert value


async def test_feed_sample_list():
    piece = htypes.sample_list.feed_sample_list()
    feed = feed_factory(piece)
    value = sample_list.feed_sample_list(piece, feed)
    assert value
    await feed.wait_for_diffs(count=1)
