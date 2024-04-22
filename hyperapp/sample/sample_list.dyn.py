import asyncio

from . import htypes
from .code.list_diff import ListDiff


def sample_list(piece):
    return [
        htypes.sample_list.item(1, "First sample"),
        htypes.sample_list.item(2, "Second sample"),
        htypes.sample_list.item(3, "Third sample"),
        ]


async def open_sample_fn_list():
    return htypes.sample_list.sample_list()


async def _send_diff(feed):
    await asyncio.sleep(1)
    item = htypes.sample_list.item(4, "Sample item #4")
    await feed.send(ListDiff.Append(item))


def feed_sample_list(piece, feed):
    asyncio.create_task(_send_diff(feed))
    return [
        htypes.sample_list.item(1, "First sample"),
        htypes.sample_list.item(2, "Second sample"),
        htypes.sample_list.item(3, "Third sample"),
        ]


async def open_feed_sample_fn_list():
    return htypes.sample_list.feed_sample_list()
