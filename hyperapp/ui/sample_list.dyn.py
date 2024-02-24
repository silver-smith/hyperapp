import asyncio
from functools import partial

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


def _send_diff(feed):
    item = htypes.sample_list.item(4, "Sample item #4")
    feed.send(ListDiff.Append(item))


def feed_sample_list(piece, feed):
    loop = asyncio.get_running_loop()
    loop.call_later(1, partial(_send_diff, feed))
    return [
        htypes.sample_list.item(1, "First sample"),
        htypes.sample_list.item(2, "Second sample"),
        htypes.sample_list.item(3, "Third sample"),
        ]


async def open_feed_sample_fn_list():
    return htypes.sample_list.feed_sample_list()
