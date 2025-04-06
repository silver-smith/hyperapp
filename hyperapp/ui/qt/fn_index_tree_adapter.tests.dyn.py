import asyncio
import logging
import threading

from hyperapp.boot.htypes import tInt

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.context import Context
from .code.tree_diff import TreeDiff
from .code.tree_visual_diff import VisualTreeDiffAppend
from .fixtures import feed_fixtures
from .tested.code import fn_index_tree_adapter

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
    model = htypes.tree_adapter_tests.sample_tree()
    ctx = Context(piece=model)
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_tree_fn),
        ctx_params=('piece', 'parent'),
        service_params=(),
        )
    adapter_piece = htypes.tree_adapter.fn_index_tree_adapter(
        item_t=mosaic.put(pyobj_creg.actor_to_piece(htypes.tree_adapter_tests.item)),
        # key_t=mosaic.put(pyobj_creg.actor_to_piece(tInt)),
        system_fn=mosaic.put(system_fn),
        )
    adapter = fn_index_tree_adapter.FnIndexTreeAdapter.from_piece(adapter_piece, model, ctx)

    assert adapter.column_count() == 2
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'text'

    assert adapter.row_count(0) == 3
    row_1_id = adapter.row_id(0, 1)
    assert adapter.cell_data(row_1_id, 0) == 2
    assert adapter.cell_data(row_1_id, 1) == "Second item"
    row_2_id = adapter.row_id(row_1_id, 2)
    assert adapter.cell_data(row_2_id, 0) == 23

    assert adapter.path_to_item_id([]) == 0
    assert adapter.path_to_item_id([0]) == adapter.row_id(0, 0)
    assert adapter.path_to_item_id([2]) == adapter.row_id(0, 2)
    assert adapter.path_to_item_id([1, 2]) == adapter.row_id(row_1_id, 2)


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
    model = htypes.tree_adapter_tests.sample_tree()
    ctx = Context(piece=model)
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_feed_tree_fn),
        ctx_params=('piece', 'parent', 'feed'),
        service_params=(),
        )
    adapter_piece = htypes.tree_adapter.fn_index_tree_adapter(
        item_t=mosaic.put(pyobj_creg.actor_to_piece(htypes.tree_adapter_tests.item)),
        # key_t=mosaic.put(pyobj_creg.actor_to_piece(tInt)),
        system_fn=mosaic.put(system_fn),
        )

    adapter = fn_index_tree_adapter.FnIndexTreeAdapter.from_piece(adapter_piece, model, ctx)
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

    diff = await asyncio.wait_for(queue.get(), timeout=5)
    assert isinstance(diff, VisualTreeDiffAppend), repr(diff)
    assert diff.parent_id == 0


_sample_fn_is_called = threading.Event()


def sample_remote_tree_fn(piece, parent):
    log.info("Sample remote tree fn: %s", piece)
    result = sample_tree_fn(piece, parent)
    _sample_fn_is_called.set()
    return result


def get_fn_called_flag():
    return _sample_fn_is_called.is_set()


def test_fn_adapter_with_remote_context(
        generate_rsa_identity,
        endpoint_registry,
        rpc_endpoint,
        rpc_call_factory,
        subprocess_rpc_server_running,
        ):

    identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(identity, rpc_endpoint)

    subprocess_name = 'test-remote-fn-tree-adapter-main'
    with subprocess_rpc_server_running(subprocess_name, identity) as process:
        log.info("Started: %r", process)

        model = htypes.tree_adapter_tests.sample_tree()
        ctx = Context(
            piece=model,
            identity=identity,
            remote_peer=process.peer,
            )
        system_fn = htypes.system_fn.ctx_fn(
            function=pyobj_creg.actor_to_ref(sample_remote_tree_fn),
            ctx_params=('piece', 'parent'),
            service_params=(),
            )
        adapter_piece = htypes.tree_adapter.fn_index_tree_adapter(
            item_t=mosaic.put(pyobj_creg.actor_to_piece(htypes.tree_adapter_tests.item)),
            # key_t=mosaic.put(pyobj_creg.actor_to_piece(tInt)),
            system_fn=mosaic.put(system_fn),
            )
        adapter = fn_index_tree_adapter.FnIndexTreeAdapter.from_piece(adapter_piece, model, ctx)

        assert adapter.column_count() == 2
        assert adapter.column_title(0) == 'id'
        assert adapter.column_title(1) == 'text'

        assert adapter.row_count(0) == 3
        row_1_id = adapter.row_id(0, 1)
        assert adapter.cell_data(row_1_id, 0) == 2
        assert adapter.cell_data(row_1_id, 1) == "Second item"
        row_2_id = adapter.row_id(row_1_id, 2)
        assert adapter.cell_data(row_2_id, 0) == 23

        get_fn_called_flag_call = rpc_call_factory(
            sender_identity=identity,
            receiver_peer=process.peer,
            servant_ref=pyobj_creg.actor_to_ref(get_fn_called_flag),
            )
        assert get_fn_called_flag_call()


def test_tree_ui_type_layout():
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_tree_fn),
        ctx_params=(),
        service_params=(),
        )
    system_fn_ref = mosaic.put(system_fn)
    piece = htypes.model.index_tree_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.fn_index_tree_adapter_tests.sample_item),
        )
    layout = fn_index_tree_adapter.tree_ui_type_layout(piece, system_fn_ref)
    assert isinstance(layout, htypes.tree.view)
