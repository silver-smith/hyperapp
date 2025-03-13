import asyncio
import logging
from functools import partial

from . import htypes
from .code.mark import mark
from .code.tree_diff import TreeDiff

log = logging.getLogger(__name__)


@mark.service
def sample_tree_data():
    return {}


def _item(parent_id, idx):
    item_id = parent_id * 10 + idx
    return htypes.sample_tree.item(item_id, f"Item #{item_id}")


@mark.service
def get_sample_tree_items(sample_tree_data, parent_id):
    try:
        return sample_tree_data[parent_id]
    except KeyError:
        pass
    items = [
        _item(parent_id, idx)
        for idx in range(5)
        ]
    sample_tree_data[parent_id] = items
    return items


@mark.model
def sample_tree(piece, parent, get_sample_tree_items):
    if parent:
        parent_id = parent.id
    else:
        parent_id = 0
    return get_sample_tree_items(parent_id)


def _index_of(item_list, item_id):
    for idx, item in enumerate(item_list):
        if item.id == item_id:
            return idx
    assert False, (item_id, item_list)


def _item_path(get_sample_tree_items, item_id):
    if item_id == 0:
        return []
    parent_id = item_id // 10
    item_list = get_sample_tree_items(parent_id)
    idx = _index_of(item_list, item_id)
    parent_path = _item_path(get_sample_tree_items, parent_id)
    return [*parent_path, idx]


@mark.command
async def remove_tree_item(piece, current_item, feed_factory, get_sample_tree_items):
    feed = feed_factory(piece)
    item_id = current_item.id
    path = _item_path(get_sample_tree_items, item_id)
    log.info("Sample tree: Remove item #%d: path=%s", item_id, path)
    parent_id = item_id // 10
    item_list = get_sample_tree_items(parent_id)
    idx = _index_of(item_list, item_id)
    del item_list[idx]
    diff = TreeDiff.Remove(path)
    await feed.send(diff)
    

@mark.global_command
async def open_sample_fn_tree():
    return htypes.sample_tree.sample_tree()


async def _send_diff(path, base, feed, idx):
    await asyncio.sleep(1)
    item = htypes.sample_tree.item(base*10 + idx, f"Sample item #{idx}")
    await feed.send(TreeDiff.Append(path, item))
    if idx < 9:
        asyncio.create_task(_send_diff(path, base, feed, idx + 1))


@mark.model
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
    asyncio.create_task(_send_diff(path, base, feed, 4))
    return [
        htypes.sample_tree.item(base*10 + 1, "First sample"),
        htypes.sample_tree.item(base*10 + 2, "Second sample"),
        htypes.sample_tree.item(base*10 + 3, "Third sample"),
        ]


@mark.global_command
async def open_feed_sample_fn_tree():
    return htypes.sample_tree.feed_sample_tree()
