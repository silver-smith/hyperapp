from unittest.mock import Mock

from hyperapp.common.htypes import tInt

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.context import Context
from .fixtures import qapp_fixtures, feed_fixtures
from .tested.code import tree


def _sample_tree_fn(piece, parent):
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


def _make_adapter_piece():
    return htypes.tree_adapter.fn_index_tree_adapter(
        element_t=mosaic.put(pyobj_creg.actor_to_piece(htypes.tree_tests.item)),
        key_t=mosaic.put(pyobj_creg.actor_to_piece(tInt)),
        function=pyobj_creg.actor_to_ref(_sample_tree_fn),
        params=('piece', 'parent'),
        )


def _make_piece():
    adapter_piece = _make_adapter_piece()
    return htypes.tree.view(mosaic.put(adapter_piece))


def test_tree(qapp, model_view_creg):
    ctx = Context()
    piece = _make_piece()
    model = htypes.tree_tests.sample_tree()
    state = None
    view = model_view_creg.animate(piece, model, ctx)
    view.set_controller_hook(Mock())
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert isinstance(state, htypes.tree.state)
    model_state = view._model_state(widget)
    assert model_state
