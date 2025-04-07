import asyncio
import logging
import threading

from hyperapp.boot.htypes import tInt

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.tree_diff import TreeDiff
from .code.tree_visual_diff import VisualTreeDiffAppend
from .fixtures import feed_fixtures
from .tested.code import fn_tree_adapter

log = logging.getLogger(__name__)


@mark.fixture
def model():
    return htypes.tree_adapter_tests.sample_tree()


def sample_index_tree_model(piece, parent):
    log.info("Sample index tree fn: %s @ %s", piece, parent)
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


@mark.fixture
def sample_index_tree_model_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_index_tree_model),
        ctx_params=('piece', 'parent'),
        service_params=(),
        )


def sample_key_tree_model(piece, current_path):
    log.info("Sample key tree fn: %s @ %s", piece, current_path)
    assert isinstance(piece, htypes.tree_adapter_tests.sample_tree), repr(piece)
    if current_path:
        base = current_path[-1]
    else:
        base = 0
    return [
        htypes.tree_adapter_tests.item(base*10 + 1, "First item"),
        htypes.tree_adapter_tests.item(base*10 + 2, "Second item"),
        htypes.tree_adapter_tests.item(base*10 + 3, "Third item"),
        ]


@mark.fixture
def sample_key_tree_model_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_key_tree_model),
        ctx_params=('piece', 'current_path'),
        service_params=(),
        )


@mark.fixture
def ctx(model):
    return Context(
        piece=model,
        )


@mark.fixture
def index_adapter(model, ctx, sample_index_tree_model_fn):
    item_t = htypes.tree_adapter_tests.item
    piece = htypes.tree_adapter.fn_index_tree_adapter(
        item_t=pyobj_creg.actor_to_ref(item_t),
        system_fn=mosaic.put(sample_index_tree_model_fn),
        )
    return fn_tree_adapter.FnIndexTreeAdapter.from_piece(piece, model, ctx)


async def test_index_adapter_contents(index_adapter):
    adapter = index_adapter

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

    async def wait_for_diff(self):
        return await asyncio.wait_for(self._queue.get(), timeout=5)


@mark.fixture
def subscriber():
    queue = asyncio.Queue()
    return Subscriber(queue)


@mark.fixture
def feed(feed_factory, model):
    return feed_factory(model)


async def test_index_adapter_append_diff(index_adapter, subscriber, feed):
    adapter = index_adapter
    adapter.subscribe(subscriber)

    item = htypes.tree_adapter_tests.item(4, "Forth item")
    await feed.send(TreeDiff.Append((), item))

    diff = await subscriber.wait_for_diff()
    assert isinstance(diff, VisualTreeDiffAppend), repr(diff)
    assert diff.parent_id == 0


async def test_fn_key_adapter(model, sample_key_tree_model_fn):
    ctx = Context(piece=model)
    adapter_piece = htypes.tree_adapter.fn_key_tree_adapter(
        item_t=mosaic.put(pyobj_creg.actor_to_piece(htypes.tree_adapter_tests.item)),
        system_fn=mosaic.put(sample_key_tree_model_fn),
        key_field='id',
        key_field_t=pyobj_creg.actor_to_ref(htypes.builtin.int),
        )
    adapter = fn_tree_adapter.FnKeyTreeAdapter.from_piece(adapter_piece, model, ctx)

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

    return

    queue = asyncio.Queue()
    subscriber = Subscriber(queue)
    adapter.subscribe(subscriber)

    feed = feed_factory(model)
    asyncio.create_task(_send_append_diff(feed))

    diff = await asyncio.wait_for(queue.get(), timeout=5)
    assert isinstance(diff, VisualTreeDiffAppend), repr(diff)
    assert diff.parent_id == 0


_sample_fn_is_called = threading.Event()


def sample_remote_tree_fn(piece, parent):
    log.info("Sample remote tree fn: %s", piece)
    result = sample_index_tree_model(piece, parent)
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
        model,
        ):

    identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(identity, rpc_endpoint)

    subprocess_name = 'test-remote-fn-tree-adapter-main'
    with subprocess_rpc_server_running(subprocess_name, identity) as process:
        log.info("Started: %r", process)

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
            system_fn=mosaic.put(system_fn),
            )
        adapter = fn_tree_adapter.FnIndexTreeAdapter.from_piece(adapter_piece, model, ctx)

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


def test_index_tree_ui_type_layout(sample_index_tree_model_fn):
    system_fn_ref = mosaic.put(sample_index_tree_model_fn)
    piece = htypes.model.index_tree_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.tree_adapter_tests.item),
        )
    layout = fn_tree_adapter.index_tree_ui_type_layout(piece, system_fn_ref)
    assert isinstance(layout, htypes.tree.view)


def test_key_tree_ui_type_layout(sample_key_tree_model_fn):
    system_fn_ref = mosaic.put(sample_key_tree_model_fn)
    piece = htypes.model.key_tree_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.tree_adapter_tests.item),
        key_field='id',
        key_field_t=pyobj_creg.actor_to_ref(htypes.builtin.int),
        )
    layout = fn_tree_adapter.key_tree_ui_type_layout(piece, system_fn_ref)
    assert isinstance(layout, htypes.tree.view)
