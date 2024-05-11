import asyncio
import logging
from functools import partial

from hyperapp.common.htypes import tInt

from . import htypes
from .services import (
    endpoint_registry,
    fn_to_ref,
    generate_rsa_identity,
    mosaic,
    pyobj_creg,
    rpc_endpoint_factory,
    subprocess_rpc_server_running,
    )
from .code.context import Context
from .code.tree_diff import TreeDiff
from .code.tree import VisualTreeDiffAppend
from .tested.code import tree_adapter

log = logging.getLogger(__name__)


def sample_tree_fn(piece, parent):
    log.info("Sample tree fn: %s", piece)
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
    model = htypes.tree_adapter_tests.sample_tree()
    adapter_piece = htypes.tree_adapter.fn_index_tree_adapter(
        element_t=mosaic.put(pyobj_creg.reverse_resolve(htypes.tree_adapter_tests.item)),
        key_t=mosaic.put(pyobj_creg.reverse_resolve(tInt)),
        function=fn_to_ref(sample_tree_fn),
        params=('piece', 'parent'),
        )
    adapter = tree_adapter.FnIndexTreeAdapter.from_piece(adapter_piece, model, ctx)

    assert adapter.column_count() == 2
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'text'

    assert adapter.row_count(0) == 3
    row_1_id = adapter.row_id(0, 1)
    assert adapter.cell_data(row_1_id, 0) == 2
    assert adapter.cell_data(row_1_id, 1) == "Second item"
    row_2_id = adapter.row_id(row_1_id, 2)
    assert adapter.cell_data(row_2_id, 0) == 23


class Subscriber:

    def __init__(self, queue):
        self._queue = queue

    def process_diff(self, diff):
        self._queue.put_nowait(diff)


async def _send_diff(feed, path, base):
    item = htypes.tree_adapter_tests.item(base*10 + 4, "Forth item")
    await feed.send(TreeDiff.Append(path, item))


def sample_feed_tree_fn(piece, parent, feed):
    log.info("Sample feed tree fn: %s", piece)
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
    asyncio.create_task(_send_diff(feed, path, base))
    return [
        htypes.tree_adapter_tests.item(base*10 + 1, "First item"),
        htypes.tree_adapter_tests.item(base*10 + 2, "Second item"),
        htypes.tree_adapter_tests.item(base*10 + 3, "Third item"),
        ]


async def test_feed_fn_adapter():
    ctx = Context()
    model = htypes.tree_adapter_tests.sample_tree()
    adapter_piece = htypes.tree_adapter.fn_index_tree_adapter(
        element_t=mosaic.put(pyobj_creg.reverse_resolve(htypes.tree_adapter_tests.item)),
        key_t=mosaic.put(pyobj_creg.reverse_resolve(tInt)),
        function=fn_to_ref(sample_feed_tree_fn),
        params=('piece', 'parent', 'feed'),
        )

    adapter = tree_adapter.FnIndexTreeAdapter.from_piece(adapter_piece, model, ctx)
    queue = asyncio.Queue()
    subscriber = Subscriber(queue)
    adapter.subscribe(subscriber)

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


def test_remote_fn_adapter():

    identity = generate_rsa_identity(fast=True)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)

    ctx = Context(
        identity=identity,
        rpc_endpoint=rpc_endpoint,
        )

    subprocess_name = 'test-remote-fn-tree-adapter-main'
    with subprocess_rpc_server_running(subprocess_name, rpc_endpoint, identity) as process:
        log.info("Started: %r", process)

        model = htypes.tree_adapter_tests.sample_tree()
        adapter_piece = htypes.tree_adapter.remote_fn_index_tree_adapter(
            element_t=mosaic.put(pyobj_creg.reverse_resolve(htypes.tree_adapter_tests.item)),
            key_t=mosaic.put(pyobj_creg.reverse_resolve(tInt)),
            function=fn_to_ref(sample_tree_fn),
            remote_peer=mosaic.put(process.peer.piece),
            params=('piece', 'parent'),
            )
        adapter = tree_adapter.RemoteFnIndexTreeAdapter.from_piece(adapter_piece, model, ctx)

        assert adapter.column_count() == 2
        assert adapter.column_title(0) == 'id'
        assert adapter.column_title(1) == 'text'

        assert adapter.row_count(0) == 3
        row_1_id = adapter.row_id(0, 1)
        assert adapter.cell_data(row_1_id, 0) == 2
        assert adapter.cell_data(row_1_id, 1) == "Second item"
        row_2_id = adapter.row_id(row_1_id, 2)
        assert adapter.cell_data(row_2_id, 0) == 23
