import logging
import threading

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .fixtures import feed_fixtures
from .tested.code import record_adapter

log = logging.getLogger(__name__)


@mark.fixture
def ctx():
    return Context()


def test_static_adapter(ctx):
    model = htypes.record_adapter_tests.item(123, "Sample static item")
    record_t_res = pyobj_creg.actor_to_piece(htypes.record_adapter_tests.item)
    adapter_piece = htypes.record_adapter.static_record_adapter(
        record_t=mosaic.put(record_t_res),
        )
    adapter = record_adapter.StaticRecordAdapter.from_piece(adapter_piece, model, ctx)
    assert adapter.record_t == htypes.record_adapter_tests.item
    assert adapter.get_field('id') == 123
    assert adapter.get_field('text') == "Sample static item"


_sample_model_is_called = threading.Event()


def _sample_record_model(piece):
    log.info("Sample record fn: %s", piece)
    assert isinstance(piece, htypes.record_adapter_tests.sample_record), repr(piece)
    _sample_model_is_called.set()
    return htypes.record_adapter_tests.item(123, "Sample fn item")


def get_model_called_flag():
    return _sample_model_is_called.is_set()


@mark.fixture
def sample_record_model_fn(rpc_system_call_factory):
    return ContextFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=('piece',),
        service_params=(),
        raw_fn=_sample_record_model,
        )


def test_local_fn_adapter(ctx, sample_record_model_fn):
    model = htypes.record_adapter_tests.sample_record()
    record_t_res = pyobj_creg.actor_to_piece(htypes.record_adapter_tests.item)
    adapter_piece = htypes.record_adapter.fn_record_adapter(
        record_t=mosaic.put(record_t_res),
        system_fn=mosaic.put(sample_record_model_fn.piece),
        )
    adapter = record_adapter.FnRecordAdapter.from_piece(adapter_piece, model, ctx)

    assert adapter.record_t == htypes.record_adapter_tests.item
    assert adapter.get_field('id') == 123
    assert adapter.get_field('text') == "Sample fn item"


def test_remote_fn_adapter(
        generate_rsa_identity,
        endpoint_registry,
        rpc_endpoint,
        rpc_call_factory,
        subprocess_rpc_server_running,
        ctx,
        sample_record_model_fn,
        ):
    identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(identity, rpc_endpoint)

    real_model = htypes.record_adapter_tests.sample_record()
    record_t_res = pyobj_creg.actor_to_piece(htypes.record_adapter_tests.item)
    adapter_piece = htypes.record_adapter.fn_record_adapter(
        record_t=mosaic.put(record_t_res),
        system_fn=mosaic.put(sample_record_model_fn.piece),
        )

    subprocess_name = 'test-remote-fn-record-adapter-main'
    with subprocess_rpc_server_running(subprocess_name, identity) as process:
        log.info("Started: %r", process)

        model = htypes.model.remote_model(
            model=mosaic.put(real_model),
            remote_peer=mosaic.put(process.peer.piece),
            )
        ctx = Context(
            model=model,
            piece=model,
            identity=identity,
            )

        adapter = record_adapter.FnRecordAdapter.from_piece(adapter_piece, model, ctx)

        assert adapter.record_t == htypes.record_adapter_tests.item
        assert adapter.get_field('id') == 123
        assert adapter.get_field('text') == "Sample fn item"

        get_model_called_flag_call = rpc_call_factory(
            sender_identity=identity,
            receiver_peer=process.peer,
            servant_ref=pyobj_creg.actor_to_ref(get_model_called_flag),
            )
        assert get_model_called_flag_call()
