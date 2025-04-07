import asyncio
import logging
import threading
from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.list_diff import IndexListDiff, KeyListDiff
from .fixtures import feed_fixtures
from .tested.code import fn_list_adapter

log = logging.getLogger(__name__)


def sample_list_model(piece):
    log.info("Sample list fn: %s", piece)
    assert isinstance(piece, htypes.list_adapter_tests.sample_list), repr(piece)
    return [
        htypes.list_adapter_tests.item(11, "first", "First item"),
        htypes.list_adapter_tests.item(22, "second", "Second item"),
        htypes.list_adapter_tests.item(33, "third", "Third item"),
        ]


@mark.fixture
def sample_list_model_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_list_model),
        ctx_params=('piece',),
        service_params=(),
        )


@mark.fixture.obj
def model_t():
    return htypes.list_adapter_tests.sample_list


@mark.fixture
def model(model_t):
    return model_t()


@mark.config_fixture('column_visible_reg')
def column_visible_reg_config(model_t):
    key = htypes.column.column_k(
        model_t=pyobj_creg.actor_to_ref(model_t),
        column_name='xdesc',
        )
    return {key: False}


@mark.fixture
def ctx(model):
    return Context(
        piece=model,
        )


class Subscriber:

    def __init__(self, queue):
        self._queue = queue

    def process_diff(self, diff):
        self._queue.put_nowait(diff)


async def _send_append_diff(feed):
    item = htypes.list_adapter_tests.item(44, "Forth diff", "Sample item #4")
    await feed.send(IndexListDiff.Append(item))


async def test_index_fn_adapter(feed_factory, sample_list_model_fn, model, ctx):
    adapter_piece = htypes.list_adapter.index_fn_list_adapter(
        item_t=mosaic.put(pyobj_creg.actor_to_piece(htypes.list_adapter_tests.item)),
        system_fn=mosaic.put(sample_list_model_fn),
        )
    adapter = fn_list_adapter.FnIndexListAdapter.from_piece(adapter_piece, model, ctx)

    assert adapter.column_count() == 2
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'text'
    assert adapter.row_count() == 3
    assert adapter.cell_data(1, 0) == 22
    assert adapter.cell_data(2, 1) == "third"

    queue = asyncio.Queue()
    subscriber = Subscriber(queue)
    adapter.subscribe(subscriber)

    feed = feed_factory(model)
    asyncio.create_task(_send_append_diff(feed))

    diff = await asyncio.wait_for(queue.get(), timeout=5)
    assert isinstance(diff, IndexListDiff.Append), repr(diff)
    assert diff.item.id == 44


async def _send_replace_diff(feed):
    item = htypes.list_adapter_tests.item(22, "Another second", "New second")
    await feed.send(KeyListDiff.Replace(22, item))


async def test_key_fn_adapter(feed_factory, sample_list_model_fn, model, ctx):
    adapter_piece = htypes.list_adapter.key_fn_list_adapter(
        item_t=mosaic.put(pyobj_creg.actor_to_piece(htypes.list_adapter_tests.item)),
        key_field='id',
        key_field_t=pyobj_creg.actor_to_ref(htypes.builtin.int),
        system_fn=mosaic.put(sample_list_model_fn),
        )
    adapter = fn_list_adapter.FnKeyListAdapter.from_piece(adapter_piece, model, ctx)

    assert adapter.column_count() == 2
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'text'
    assert adapter.row_count() == 3
    assert adapter.cell_data(1, 0) == 22
    assert adapter.cell_data(2, 1) == "third"

    queue = asyncio.Queue()
    subscriber = Subscriber(queue)
    adapter.subscribe(subscriber)

    feed = feed_factory(model)
    asyncio.create_task(_send_replace_diff(feed))

    diff = await asyncio.wait_for(queue.get(), timeout=5)
    assert isinstance(diff, IndexListDiff.Replace), repr(diff)
    assert diff.item.id == 22
    assert diff.idx == 1


_sample_fn_is_called = threading.Event()


def sample_remote_list_model(piece):
    log.info("Sample remote list fn: %s", piece)
    result = sample_list_model(piece)
    _sample_fn_is_called.set()
    return result


@mark.fixture
def sample_remote_list_model_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_remote_list_model),
        ctx_params=('piece',),
        service_params=(),
        )


def get_fn_called_flag():
    return _sample_fn_is_called.is_set()


def test_fn_adapter_with_remote_model(
        generate_rsa_identity,
        endpoint_registry,
        rpc_endpoint,
        rpc_call_factory,
        subprocess_rpc_server_running,
        sample_remote_list_model_fn,
        ):

    identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(identity, rpc_endpoint)

    subprocess_name = 'test-remote-fn-list-adapter-main'
    with subprocess_rpc_server_running(subprocess_name, identity) as process:
        log.info("Started: %r", process)

        real_model = htypes.list_adapter_tests.sample_list()
        model = htypes.model.remote_model(
            model=mosaic.put(real_model),
            remote_peer=mosaic.put(process.peer.piece),
            )
        ctx = Context(
            piece=model,
            identity=identity,
            )
        adapter_piece = htypes.list_adapter.index_fn_list_adapter(
            item_t=mosaic.put(pyobj_creg.actor_to_piece(htypes.list_adapter_tests.item)),
            system_fn=mosaic.put(sample_remote_list_model_fn),
            )
        adapter = fn_list_adapter.FnIndexListAdapter.from_piece(adapter_piece, model, ctx)

        assert adapter.column_count() == 2
        assert adapter.column_title(0) == 'id'
        assert adapter.column_title(1) == 'text'

        assert adapter.row_count() == 3
        assert adapter.cell_data(1, 0) == 22
        assert adapter.cell_data(2, 1) == "third"

        get_fn_called_flag_call = rpc_call_factory(
            sender_identity=identity,
            receiver_peer=process.peer,
            servant_ref=pyobj_creg.actor_to_ref(get_fn_called_flag),
            )
        assert get_fn_called_flag_call()


def test_fn_adapter_with_remote_context(
        generate_rsa_identity,
        endpoint_registry,
        rpc_endpoint,
        rpc_call_factory,
        subprocess_rpc_server_running,
        sample_remote_list_model_fn,
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
        adapter_piece = htypes.list_adapter.index_fn_list_adapter(
            item_t=mosaic.put(pyobj_creg.actor_to_piece(htypes.list_adapter_tests.item)),
            system_fn=mosaic.put(sample_remote_list_model_fn),
            )
        adapter = fn_list_adapter.FnIndexListAdapter.from_piece(adapter_piece, model, ctx)

        assert adapter.column_count() == 2
        assert adapter.column_title(0) == 'id'
        assert adapter.column_title(1) == 'text'

        assert adapter.row_count() == 3
        assert adapter.cell_data(1, 0) == 22
        assert adapter.cell_data(2, 1) == "third"

        get_fn_called_flag_call = rpc_call_factory(
            sender_identity=identity,
            receiver_peer=process.peer,
            servant_ref=pyobj_creg.actor_to_ref(get_fn_called_flag),
            )
        assert get_fn_called_flag_call()


def test_index_list_ui_type_layout(sample_list_model_fn):
    system_fn_ref = mosaic.put(sample_list_model_fn)
    piece = htypes.model.index_list_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.list_adapter_tests.item),
        )
    layout = fn_list_adapter.index_list_ui_type_layout(piece, system_fn_ref)
    assert isinstance(layout, htypes.list.view)


def test_key_list_ui_type_layout(sample_list_model_fn):
    system_fn_ref = mosaic.put(sample_list_model_fn)
    piece = htypes.model.key_list_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.list_adapter_tests.item),
        key_field='id',
        key_field_t=pyobj_creg.actor_to_ref(htypes.builtin.int),
        )
    layout = fn_list_adapter.key_list_ui_type_layout(piece, system_fn_ref)
    assert isinstance(layout, htypes.list.view)
