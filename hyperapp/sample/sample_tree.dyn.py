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
    item_id = parent_id*10 + idx + 1
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
    log.info("Sample tree: Remove item #%d", item_id)
    path = _item_path(get_sample_tree_items, item_id)
    log.info("Sample tree: Item #%d path: %s", item_id, path)
    parent_id = item_id // 10
    item_list = get_sample_tree_items(parent_id)
    idx = _index_of(item_list, item_id)
    del item_list[idx]
    diff = TreeDiff.Remove(path)
    await feed.send(diff)


@mark.command
async def append_tree_item(piece, current_item, feed_factory, get_sample_tree_items):
    feed = feed_factory(piece)
    item_id = current_item.id
    parent_id = item_id // 10
    log.info("Sample tree: Append item to parent #%d", parent_id)
    path = _item_path(get_sample_tree_items, parent_id)
    log.info("Sample tree: Item #%d path: %s", parent_id, path)
    item_list = get_sample_tree_items(parent_id)
    idx = len(item_list)
    if idx >= 9:
        return
    new_id = parent_id*10 + idx + 1
    new_item = htypes.sample_tree.item(new_id, f"New item #{new_id}")
    item_list.append(new_item)
    diff = TreeDiff.Append(path, new_item)
    await feed.send(diff)


@mark.command
async def insert_tree_item(piece, current_item, feed_factory, get_sample_tree_items):
    feed = feed_factory(piece)
    item_id = current_item.id
    log.info("Sample tree: Insert to item #%d", item_id)
    path = _item_path(get_sample_tree_items, item_id)
    log.info("Sample tree: Item #%d path: %s", item_id, path)
    parent_id = item_id // 10
    item_list = get_sample_tree_items(parent_id)
    if len(item_list) >= 10:
        return
    idx = _index_of(item_list, item_id)
    new_id = parent_id*10 + idx + 1
    new_item = htypes.sample_tree.item(new_id, f"New item #{new_id}")
    item_list.insert(idx, new_item)
    diff = TreeDiff.Insert(path, new_item)
    await feed.send(diff)
    

@mark.global_command
async def open_sample_fn_tree():
    return htypes.sample_tree.sample_tree()


@mark.actor.formatter_creg
def format_model(piece):
    return "Sample tree"
