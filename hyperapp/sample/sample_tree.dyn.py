import asyncio
from functools import partial

from . import htypes
from .code.tree_diff import TreeDiff


def sample_tree(piece, parent):
    if parent:
        base = parent.id
    else:
        base = 0
    return [
        htypes.sample_tree.item(base*10 + 1, "First sample"),
        htypes.sample_tree.item(base*10 + 2, "Second sample"),
        htypes.sample_tree.item(base*10 + 3, "Third sample"),
        ]


async def open_sample_fn_tree():
    return htypes.sample_tree.sample_tree()


def _send_diff(path, base, feed, idx):
    item = htypes.sample_tree.item(base*10 + idx, f"Sample item #{idx}")
    feed.send(TreeDiff.Append(path, item))
    if idx < 9:
        loop = asyncio.get_running_loop()
        loop.call_later(1, partial(_send_diff, path, base, feed, idx + 1))


def feed_sample_tree(piece, parent, feed):
    loop = asyncio.get_running_loop()
    if parent:
        base = parent.id
    else:
        base = 0
    path = []
    i = base
    while i:
        path = [i % 10 - 1, *path]
        i = i // 10
    loop.call_later(1, partial(_send_diff, path, base, feed, 4))
    return [
        htypes.sample_tree.item(base*10 + 1, "First sample"),
        htypes.sample_tree.item(base*10 + 2, "Second sample"),
        htypes.sample_tree.item(base*10 + 3, "Third sample"),
        ]


async def open_feed_sample_fn_tree():
    return htypes.sample_tree.feed_sample_tree()
