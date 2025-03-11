import asyncio

from . import htypes
from .code.mark import mark
from .code.list_diff import ListDiff


@mark.model
def sample_list(piece):
    return [
        htypes.sample_list.item(1, "first", "First sample"),
        htypes.sample_list.item(2, "second", "Second sample"),
        htypes.sample_list.item(3, "third", "Third sample"),
        ]


@mark.global_command
async def open_sample_fn_list():
    return htypes.sample_list.sample_list()


async def _send_diff(feed):
    await asyncio.sleep(1)
    item = htypes.sample_list.item(4, "fourth","Sample item #4")
    await feed.send(ListDiff.Append(item))


@mark.model
def feed_sample_list(piece, feed):
    asyncio.create_task(_send_diff(feed))
    return [
        htypes.sample_list.item(1, "first", "First sample"),
        htypes.sample_list.item(2, "second", "Second sample"),
        htypes.sample_list.item(3, "third", "Third sample"),
        ]


@mark.global_command
async def open_feed_sample_fn_list():
    return htypes.sample_list.feed_sample_list()


@mark.actor.formatter_creg
def format_model(piece):
    return "Sample list"


@mark.actor.formatter_creg
def format_feed_model(piece):
    return "Sample feed list"
