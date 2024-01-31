import asyncio
from functools import partial

from . import htypes
# from .code.tree_diff import TreeDiffAppend


def sample_tree(piece, parent_key):
    if parent_key is None:
        base = 0
    else:
        base = parent_key[-1]
    return [
        htypes.sample_tree.item(base*10 + 1, "First sample"),
        htypes.sample_tree.item(base*10 + 2, "Second sample"),
        htypes.sample_tree.item(base*10 + 3, "Third sample"),
        ]


async def open_sample_fn_tree():
    return htypes.sample_tree.sample_tree()


def _send_diff(feed):
    item = htypes.sample_tree.item(4, "Sample item #4")
    # feed.send(TreeDiffAppend(item))
    feed.send(None)


def feed_sample_tree(piece, feed, parent_key):
    loop = asyncio.get_running_loop()
    loop.call_later(1, partial(_send_diff, feed))
    base = parent_key or 0
    return [
        htypes.sample_tree.item(base*10 + 1, "First sample"),
        htypes.sample_tree.item(base*10 + 2, "Second sample"),
        htypes.sample_tree.item(base*10 + 3, "Third sample"),
        ]


async def open_feed_sample_fn_tree():
    return htypes.sample_tree.feed_sample_tree()
