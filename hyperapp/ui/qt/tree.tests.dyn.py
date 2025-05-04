from unittest.mock import Mock

from hyperapp.boot.htypes import tInt

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .fixtures import qapp_fixtures, feed_fixtures
from .tested.code import tree


def sample_index_tree_model(piece, parent):
    assert isinstance(piece, htypes.tree_tests.sample_tree), repr(piece)
    if parent:
        base = parent.id
    else:
        base = 0
    return [
        htypes.tree_tests.index_item(base*10 + 1, "First item"),
        htypes.tree_tests.index_item(base*10 + 2, "Second item"),
        htypes.tree_tests.index_item(base*10 + 3, "Third item"),
        ]


@mark.fixture
def sample_index_tree_model_fn(rpc_system_call_factory):
    return ContextFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=('piece', 'parent'),
        service_params=(),
        raw_fn=sample_index_tree_model,
        )


def sample_key_tree_model(piece, current_path, sample_ctx):
    log.info("Sample key tree fn: %s @ %s", piece, current_path)
    assert isinstance(piece, htypes.tree_tests.sample_tree), repr(piece)
    assert sample_ctx == 'sample-ctx'
    if current_path:
        base = int(current_path[-1])
    else:
        base = 0
    return [
        htypes.tree_tests.key_item(str(base*10 + 1), "First item"),
        htypes.tree_tests.key_item(str(base*10 + 2), "Second item"),
        htypes.tree_tests.key_item(str(base*10 + 3), "Third item"),
        ]


@mark.fixture
def sample_key_tree_model_fn(rpc_system_call_factory):
    return ContextFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=('piece', 'current_path', 'sample_ctx'),
        service_params=(),
        raw_fn=sample_key_tree_model,
        )


@mark.fixture
def adapter_piece(sample_index_tree_model_fn):
    return htypes.tree_adapter.fn_index_tree_adapter(
        item_t=mosaic.put(pyobj_creg.actor_to_piece(htypes.tree_tests.index_item)),
        # key_t=mosaic.put(pyobj_creg.actor_to_piece(tInt)),
        system_fn=mosaic.put(sample_index_tree_model_fn.piece),
        )


@mark.fixture
def piece(adapter_piece):
    return htypes.tree.view(
        adapter=mosaic.put(adapter_piece),
        )


def test_tree(qapp, piece):
    ctx = Context()
    model = htypes.tree_tests.sample_tree()
    state = None
    view = tree.TreeView.from_piece(piece, model, ctx)
    view.set_controller_hook(Mock())
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert isinstance(state, htypes.tree.state)
    model_state = view._model_state(widget)
    assert model_state


def test_index_ui_type_layout(sample_index_tree_model_fn):
    piece = htypes.model.index_tree_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.tree_tests.index_item),
        )
    layout = tree.index_tree_ui_type_layout(piece, sample_index_tree_model_fn)
    assert isinstance(layout, htypes.tree.view)


def test_key_ui_type_layout(sample_key_tree_model_fn):
    piece = htypes.model.key_tree_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.tree_tests.key_item),
        key_field='key',
        key_field_t=pyobj_creg.actor_to_ref(htypes.builtin.string),
        )
    layout = tree.key_tree_ui_type_layout(piece, sample_key_tree_model_fn)
    assert isinstance(layout, htypes.tree.view)
