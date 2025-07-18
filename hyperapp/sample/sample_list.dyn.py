import asyncio
import logging

from . import htypes
from .code.mark import mark
from .code.list_diff import IndexListDiff

log = logging.getLogger(__name__)


@mark.model
def sample_list(piece):
    log.info("Sample list: Called model")
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
    feed.send(IndexListDiff.Append(item))


@mark.model
def feed_sample_list(piece, feed_factory):
    feed = feed_factory(piece)
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
