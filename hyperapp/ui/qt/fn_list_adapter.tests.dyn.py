import asyncio
import logging
import threading

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.context import Context
from .code.list_diff import ListDiff
from .fixtures import feed_fixtures
from .tested.code import fn_list_adapter

log = logging.getLogger(__name__)


def sample_list_fn(piece):
    log.info("Sample list fn: %s", piece)
    assert isinstance(piece, htypes.list_adapter_tests.sample_list), repr(piece)
    return [
        htypes.list_adapter_tests.item(11, "First item"),
        htypes.list_adapter_tests.item(22, "Second item"),
        htypes.list_adapter_tests.item(33, "Third item"),
        ]


def test_fn_adapter(ui_adapter_creg):
    model = htypes.list_adapter_tests.sample_list()
    ctx = Context(piece=model)
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_list_fn),
        ctx_params=('piece',),
        service_params=(),
        )
    adapter_piece = htypes.list_adapter.fn_list_adapter(
        item_t=mosaic.put(pyobj_creg.actor_to_piece(htypes.list_adapter_tests.item)),
        system_fn=mosaic.put(system_fn),
        )
    adapter = ui_adapter_creg.animate(adapter_piece, model, ctx)
    assert adapter.column_count() == 2
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'text'
    assert adapter.row_count() == 3
    assert adapter.cell_data(1, 0) == 22
    assert adapter.cell_data(2, 1) == "Third item"


class Subscriber:

    def __init__(self, queue):
        self._queue = queue

    def process_diff(self, diff):
        self._queue.put_nowait(diff)


async def _send_diff(feed):
    item = htypes.sample_list.item(44, "Sample item #4")
    await feed.send(ListDiff.Append(item))


def sample_feed_list_fn(piece, feed):
    log.info("Sample feed list fn: %s", piece)
    assert isinstance(piece, htypes.list_adapter_tests.sample_list), repr(piece)
    asyncio.create_task(_send_diff(feed))
    return [
        htypes.list_adapter_tests.item(11, "First item"),
        htypes.list_adapter_tests.item(22, "Second item"),
        htypes.list_adapter_tests.item(33, "Third item"),
        ]


async def test_feed_fn_adapter(ui_adapter_creg):
    model = htypes.list_adapter_tests.sample_list()
    ctx = Context(piece=model)
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_feed_list_fn),
        ctx_params=('piece', 'feed'),
        service_params=(),
        )
    adapter_piece = htypes.list_adapter.fn_list_adapter(
        item_t=mosaic.put(pyobj_creg.actor_to_piece(htypes.list_adapter_tests.item)),
        system_fn=mosaic.put(system_fn),
        )

    adapter = ui_adapter_creg.animate(adapter_piece, model, ctx)
    queue = asyncio.Queue()
    subscriber = Subscriber(queue)
    adapter.subscribe(subscriber)

    assert adapter.column_count() == 2
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'text'

    assert adapter.row_count() == 3
    assert adapter.cell_data(1, 0) == 22
    assert adapter.cell_data(2, 1) == "Third item"

    diff = await asyncio.wait_for(queue.get(), timeout=5)
    assert isinstance(diff, ListDiff.Append), repr(diff)
    assert diff.item.id == 44


_sample_fn_is_called = threading.Event()


def sample_remote_list_fn(piece):
    log.info("Sample remote list fn: %s", piece)
    result = sample_list_fn(piece)
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
        ui_adapter_creg,
        ):

    identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(identity, rpc_endpoint)

    subprocess_name = 'test-remote-fn-list-adapter-main'
    with subprocess_rpc_server_running(subprocess_name, identity) as process:
        log.info("Started: %r", process)

        model = htypes.list_adapter_tests.sample_list()
        ctx = Context(
            piece=model,
            identity=identity,
            remote_peer=process.peer,
            )
        system_fn = htypes.system_fn.ctx_fn(
            function=pyobj_creg.actor_to_ref(sample_remote_list_fn),
            ctx_params=('piece',),
            service_params=(),
            )
        adapter_piece = htypes.list_adapter.fn_list_adapter(
            item_t=mosaic.put(pyobj_creg.actor_to_piece(htypes.list_adapter_tests.item)),
            system_fn=mosaic.put(system_fn),
            )
        adapter = ui_adapter_creg.animate(adapter_piece, model, ctx)

        assert adapter.column_count() == 2
        assert adapter.column_title(0) == 'id'
        assert adapter.column_title(1) == 'text'

        assert adapter.row_count() == 3
        assert adapter.cell_data(1, 0) == 22
        assert adapter.cell_data(2, 1) == "Third item"

        get_fn_called_flag_call = rpc_call_factory(
            sender_identity=identity,
            receiver_peer=process.peer,
            servant_ref=pyobj_creg.actor_to_ref(get_fn_called_flag),
            )
        assert get_fn_called_flag_call()


def test_list_ui_type_layout():
    system_fn = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_list_fn),
        ctx_params=(),
        service_params=(),
        )
    system_fn_ref = mosaic.put(system_fn)
    piece = htypes.model.list_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.fn_list_adapter_tests.sample_item),
        )
    layout = fn_list_adapter.list_ui_type_layout(piece, system_fn_ref)
    assert isinstance(layout, htypes.list.view)
