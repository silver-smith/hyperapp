import asyncio
from functools import partial

from hyperapp.common.htypes import tInt

from . import htypes
from .services import (
    fn_to_ref,
    mosaic,
    pyobj_creg,
    )
from .code.context import Context
from .code.tree_diff import TreeDiff
from .code.tree import VisualTreeDiffAppend
from .tested.code import tree_adapter


def sample_tree_fn(piece, parent):
    assert isinstance(piece, htypes.tree_adapter_tests.sample_tree), repr(piece)
    if parent:
        base = parent.id
    else:
        base = 0
    return [
        htypes.tree_adapter_tests.item(base*10 + 1, "First item"),
        htypes.tree_adapter_tests.item(base*10 + 2, "Second item"),
        htypes.tree_adapter_tests.item(base*10 + 3, "Third item"),
        ]


def test_fn_adapter():
    ctx = Context()
    model_piece = htypes.tree_adapter_tests.sample_tree()
    adapter_piece = htypes.tree_adapter.fn_index_tree_adapter(
        model_piece=mosaic.put(model_piece),
        element_t=mosaic.put(pyobj_creg.reverse_resolve(htypes.tree_adapter_tests.item)),
        key_t=mosaic.put(pyobj_creg.reverse_resolve(tInt)),
        function=fn_to_ref(sample_tree_fn),
        want_feed=False,
        )
    adapter = tree_adapter.FnIndexTreeAdapter.from_piece(adapter_piece, ctx)

    assert adapter.column_count() == 2
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'text'

    assert adapter.row_count(0) == 3
    row_1_id = adapter.row_id(0, 1)
    assert adapter.cell_data(row_1_id, 0) == 2
    assert adapter.cell_data(row_1_id, 1) == "Second item"
    row_2_id = adapter.row_id(row_1_id, 2)
    assert adapter.cell_data(row_2_id, 0) == 23


class MockModel:

    def __init__(self, queue):
        self._queue = queue

    def process_diff(self, diff):
        self._queue.put_nowait(diff)


def _send_diff(feed, path, base):
    item = htypes.tree_adapter_tests.item(base*10 + 4, "Forth item")
    feed.send(TreeDiff.Append(path, item))


def feed_sample_tree_fn(piece, parent, feed):
    assert isinstance(piece, htypes.tree_adapter_tests.sample_tree), repr(piece)
    if parent:
        base = parent.id
    else:
        base = 0
    path = []
    i = base
    while i:
        path = [i % 10 - 1, *path]
        i = i // 10
    loop = asyncio.get_running_loop()
    loop.call_soon(partial(_send_diff, feed, path, base))
    return [
        htypes.tree_adapter_tests.item(base*10 + 1, "First item"),
        htypes.tree_adapter_tests.item(base*10 + 2, "Second item"),
        htypes.tree_adapter_tests.item(base*10 + 3, "Third item"),
        ]


async def test_feed_fn_adapter():
    ctx = Context()
    model_piece = htypes.tree_adapter_tests.sample_tree()
    adapter_piece = htypes.tree_adapter.fn_index_tree_adapter(
        model_piece=mosaic.put(model_piece),
        element_t=mosaic.put(pyobj_creg.reverse_resolve(htypes.tree_adapter_tests.item)),
        key_t=mosaic.put(pyobj_creg.reverse_resolve(tInt)),
        function=fn_to_ref(feed_sample_tree_fn),
        want_feed=True,
        )

    adapter = tree_adapter.FnIndexTreeAdapter.from_piece(adapter_piece, ctx)
    queue = asyncio.Queue()
    model = MockModel(queue)
    adapter.subscribe(model)

    assert adapter.column_count() == 2
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'text'

    assert adapter.row_count(0) == 3
    row_1_id = adapter.row_id(0, 1)
    assert adapter.cell_data(row_1_id, 0) == 2
    assert adapter.cell_data(row_1_id, 1) == "Second item"
    row_2_id = adapter.row_id(row_1_id, 2)
    assert adapter.cell_data(row_2_id, 0) == 23

    diff = await queue.get()
    assert isinstance(diff, VisualTreeDiffAppend), repr(diff)
    assert diff.parent_id == 0
