import logging

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.context import Context
from .fixtures import feed_fixtures
from .tested.code import remote_fn_list_adapter

log = logging.getLogger(__name__)


def sample_list_fn(piece):
    log.info("Sample list fn: %s", piece)
    assert isinstance(piece, htypes.list_adapter_tests.sample_list), repr(piece)
    return [
        htypes.list_adapter_tests.item(11, "First item"),
        htypes.list_adapter_tests.item(22, "Second item"),
        htypes.list_adapter_tests.item(33, "Third item"),
        ]


def test_remote_fn_adapter(
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
            rpc_endpoint=rpc_endpoint,
            )
        system_fn = htypes.system_fn.ctx_fn(
            function=pyobj_creg.actor_to_ref(sample_list_fn),
            ctx_params=('piece',),
            service_params=(),
            )
        adapter_piece = htypes.list_adapter.remote_fn_list_adapter(
            item_t=mosaic.put(pyobj_creg.actor_to_piece(htypes.list_adapter_tests.item)),
            system_fn=mosaic.put(system_fn),
            remote_peer=mosaic.put(process.peer.piece),
            )
        adapter = ui_adapter_creg.animate(adapter_piece, model, ctx)

        assert adapter.column_count() == 2
        assert adapter.column_title(0) == 'id'
        assert adapter.column_title(1) == 'text'

        assert adapter.row_count() == 3
        assert adapter.cell_data(1, 0) == 22
        assert adapter.cell_data(2, 1) == "Third item"
