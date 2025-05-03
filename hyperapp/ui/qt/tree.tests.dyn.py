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


def _sample_tree_model(piece, parent):
    assert isinstance(piece, htypes.tree_tests.sample_tree), repr(piece)
    if parent:
        base = parent.id
    else:
        base = 0
    return [
        htypes.tree_tests.item(base*10 + 1, "First item"),
        htypes.tree_tests.item(base*10 + 2, "Second item"),
        htypes.tree_tests.item(base*10 + 3, "Third item"),
        ]


@mark.fixture
def model_fn(rpc_system_call_factory):
    return ContextFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=('piece', 'parent'),
        service_params=(),
        raw_fn=_sample_tree_model,
        )


@mark.fixture
def adapter_piece(model_fn):
    return htypes.tree_adapter.fn_index_tree_adapter(
        item_t=mosaic.put(pyobj_creg.actor_to_piece(htypes.tree_tests.item)),
        # key_t=mosaic.put(pyobj_creg.actor_to_piece(tInt)),
        system_fn=mosaic.put(model_fn.piece),
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


def test_index_layout(model_fn):
    ui_t = htypes.model.index_tree_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.tree_tests.item),
        )
    piece = tree.index_tree_ui_type_layout(ui_t, model_fn)
    assert isinstance(piece, htypes.tree.view)
