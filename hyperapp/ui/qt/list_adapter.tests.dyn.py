import asyncio
import logging
from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from . import htypes
from .services import (
    endpoint_registry,
    fn_to_ref,
    generate_rsa_identity,
    mosaic,
    pyobj_creg,
    rpc_endpoint_factory,
    subprocess_rpc_server_running,
    types,
    )
from .code.context import Context
from .code.list_diff import ListDiff
from .tested.code import list_adapter

log = logging.getLogger(__name__)


def test_static_adapter():
    ctx = Context()
    value = (
        htypes.list_tests.item(1, "First"),
        htypes.list_tests.item(2, "Second"),
        htypes.list_tests.item(3, "Third"),
        )
    t = deduce_complex_value_type(mosaic, types, value)
    piece = htypes.list_adapter.static_list_adapter(mosaic.put(value, t))
    adapter = list_adapter.StaticListAdapter.from_piece(piece, ctx)

    assert adapter.column_count() == 2
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'title'

    assert adapter.row_count() == 3
    assert adapter.cell_data(1, 0) == 2
    assert adapter.cell_data(2, 1) == "Third"


def sample_list_fn(piece):
    log.info("Sample list fn: %s", piece)
    assert isinstance(piece, htypes.list_adapter_tests.sample_list), repr(piece)
    return [
        htypes.list_adapter_tests.item(11, "First item"),
        htypes.list_adapter_tests.item(22, "Second item"),
        htypes.list_adapter_tests.item(33, "Third item"),
        ]


def test_fn_adapter():
    ctx = Context()
    model_piece = htypes.list_adapter_tests.sample_list()
    adapter_piece = htypes.list_adapter.fn_list_adapter(
        model_piece=mosaic.put(model_piece),
        element_t=mosaic.put(pyobj_creg.reverse_resolve(htypes.list_adapter_tests.item)),
        function=fn_to_ref(sample_list_fn),
        want_feed=False,
        )
    adapter = list_adapter.FnListAdapter.from_piece(adapter_piece, ctx)
    assert adapter.column_count() == 2
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'text'
    assert adapter.row_count() == 3
    assert adapter.cell_data(1, 0) == 22
    assert adapter.cell_data(2, 1) == "Third item"


class MockModel:

    def __init__(self, queue):
        self._queue = queue

    def process_diff(self, diff):
        self._queue.put_nowait(diff)


def _send_diff(feed):
    item = htypes.sample_list.item(44, "Sample item #4")
    feed.send(ListDiff.Append(item))


def sample_feed_list_fn(piece, feed):
    log.info("Sample feed list fn: %s", piece)
    assert isinstance(piece, htypes.list_adapter_tests.sample_list), repr(piece)
    loop = asyncio.get_running_loop()
    loop.call_soon(partial(_send_diff, feed))
    return [
        htypes.list_adapter_tests.item(11, "First item"),
        htypes.list_adapter_tests.item(22, "Second item"),
        htypes.list_adapter_tests.item(33, "Third item"),
        ]


async def test_feed_fn_adapter():
    ctx = Context()
    model_piece = htypes.list_adapter_tests.sample_list()
    adapter_piece = htypes.list_adapter.fn_list_adapter(
        model_piece=mosaic.put(model_piece),
        element_t=mosaic.put(pyobj_creg.reverse_resolve(htypes.list_adapter_tests.item)),
        function=fn_to_ref(sample_feed_list_fn),
        want_feed=True,
        )

    adapter = list_adapter.FnListAdapter.from_piece(adapter_piece, ctx)
    queue = asyncio.Queue()
    model = MockModel(queue)
    adapter.subscribe(model)

    assert adapter.column_count() == 2
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'text'

    assert adapter.row_count() == 3
    assert adapter.cell_data(1, 0) == 22
    assert adapter.cell_data(2, 1) == "Third item"

    diff = await queue.get()
    assert isinstance(diff, ListDiff.Append), repr(diff)
    assert diff.item.id == 44


def test_remote_fn_adapter():

    identity = generate_rsa_identity(fast=True)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)

    ctx = Context(
        identity=identity,
        rpc_endpoint=rpc_endpoint,
        )

    subprocess_name = 'test-remote-fn-list-adapter-main'
    with subprocess_rpc_server_running(subprocess_name, rpc_endpoint, identity) as process:
        log.info("Started: %r", process)

        model_piece = htypes.list_adapter_tests.sample_list()
        adapter_piece = htypes.list_adapter.remote_fn_list_adapter(
            model_piece=mosaic.put(model_piece),
            element_t=mosaic.put(pyobj_creg.reverse_resolve(htypes.list_adapter_tests.item)),
            function=fn_to_ref(sample_list_fn),
            remote_peer=mosaic.put(process.peer.piece),
            want_feed=False,
            )
        adapter = list_adapter.RemoteFnListAdapter.from_piece(adapter_piece, ctx)

        assert adapter.column_count() == 2
        assert adapter.column_title(0) == 'id'
        assert adapter.column_title(1) == 'text'

        assert adapter.row_count() == 3
        assert adapter.cell_data(1, 0) == 22
        assert adapter.cell_data(2, 1) == "Third item"
