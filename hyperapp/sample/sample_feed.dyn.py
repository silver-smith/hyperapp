import asyncio
import logging

from . import htypes
from .code.list_diff import IndexListDiff
from .code.tree_diff import TreeDiff

log = logging.getLogger(__name__)


def _send_list_diff(feed):
    log.info("Sending list diff")
    item = htypes.sample_list.item(44, "Forth diff", "Sample item #4")
    feed.send(IndexListDiff.Append(item))


def schedule_sample_list_feed(feed_factory, piece):
    feed = feed_factory(piece)
    loop = asyncio.get_running_loop()
    loop.call_soon(_send_list_diff, feed)


def _send_tree_diff(feed):
    log.info("Sending tree diff")
    item = htypes.sample_tree.item(55, "Sample item #4")
    feed.send(TreeDiff.Append([], item))


def schedule_sample_tree_feed(feed_factory, piece):
    feed = feed_factory(piece)
    loop = asyncio.get_running_loop()
    loop.call_soon(_send_tree_diff, feed)
