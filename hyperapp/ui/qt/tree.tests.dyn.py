from unittest.mock import Mock

from hyperapp.common.htypes import tInt
from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from PySide6 import QtWidgets

from . import htypes
from .services import (
    fn_to_ref,
    mosaic,
    pyobj_creg,
    types,
    )
from .code.context import Context
from .tested.code import tree


def _sample_tree_fn(piece, parent):
    assert isinstance(piece, htypes.tree_adapter_tests.sample_tree), repr(piece)
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
        element_t=mosaic.put(pyobj_creg.reverse_resolve(htypes.tree_tests.item)),
        key_t=mosaic.put(pyobj_creg.reverse_resolve(tInt)),
        function=fn_to_ref(_sample_tree_fn),
        want_feed=False,
        )


def _make_piece():
    adapter_piece = _make_adapter_piece()
    return htypes.tree.view(mosaic.put(adapter_piece))


def test_tree():
    ctx = Context()
    piece = _make_piece()
    model = htypes.tree_tests.sample_tree()
    state = None
    app = QtWidgets.QApplication()
    try:
        view = tree.TreeView.from_piece(piece, model, ctx)
        view.set_controller_hook(Mock())
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        # assert state
        model_state = view.model_state(widget)
        assert model_state
    finally:
        app.shutdown()
