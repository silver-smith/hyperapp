import asyncio
import logging

from . import htypes
from .code.list_diff import ListDiff
from .code.tree_diff import TreeDiff

log = logging.getLogger(__name__)


async def _send_list_diff(feed):
    log.info("Sending list diff")
    item = htypes.sample_list.item(44, "Sample item #4")
    await feed.send(ListDiff.Append(item))


async def schedule_sample_list_feed(feed_factory, piece):
    feed = feed_factory(piece)
    asyncio.create_task(_send_list_diff(feed))


async def _send_tree_diff(feed):
    log.info("Sending tree diff")
    item = htypes.sample_tree.item(44, "Sample item #4")
    await feed.send(TreeDiff.Append([], item))


async def schedule_sample_tree_feed(feed_factory, piece):
    feed = feed_factory(piece)
    asyncio.create_task(_send_tree_diff(feed))
