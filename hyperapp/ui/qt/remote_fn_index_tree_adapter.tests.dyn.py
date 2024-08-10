import asyncio
import logging
import threading

from hyperapp.common.htypes import tInt

from . import htypes
from .services import (
    fn_to_ref,
    mosaic,
    pyobj_creg,
    )
from .code.context import Context
from .fixtures import feed_fixtures
from .tested.code import remote_fn_index_tree_adapter

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


def test_remote_fn_adapter(
        generate_rsa_identity,
        rpc_endpoint,
        endpoint_registry,
        subprocess_rpc_server_running,
        ui_adapter_creg,
        ):

    identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(identity, rpc_endpoint)

    ctx = Context(
        identity=identity,
        rpc_endpoint=rpc_endpoint,
        )

    subprocess_name = 'test-remote-fn-tree-adapter-main'
    with subprocess_rpc_server_running(subprocess_name, identity) as process:
        log.info("Started: %r", process)

        model = htypes.tree_adapter_tests.sample_tree()
        adapter_piece = htypes.tree_adapter.remote_fn_index_tree_adapter(
            element_t=mosaic.put(pyobj_creg.actor_to_piece(htypes.tree_adapter_tests.item)),
            key_t=mosaic.put(pyobj_creg.actor_to_piece(tInt)),
            function=fn_to_ref(sample_tree_fn),
            remote_peer=mosaic.put(process.peer.piece),
            params=('piece', 'parent'),
            )
        adapter = ui_adapter_creg.animate(adapter_piece, model, ctx)

        assert adapter.column_count() == 2
        assert adapter.column_title(0) == 'id'
        assert adapter.column_title(1) == 'text'

        assert adapter.row_count(0) == 3
        row_1_id = adapter.row_id(0, 1)
        assert adapter.cell_data(row_1_id, 0) == 2
        assert adapter.cell_data(row_1_id, 1) == "Second item"
        row_2_id = adapter.row_id(row_1_id, 2)
        assert adapter.cell_data(row_2_id, 0) == 23
