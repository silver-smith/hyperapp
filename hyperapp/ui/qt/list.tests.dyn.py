from unittest.mock import Mock

from PySide6 import QtWidgets

from . import htypes
from .tested.code import list
from .services import (
    mosaic,
    types,
    )
from .code.context import Context


def make_adapter_piece():
    return htypes.list_adapter.static_list_adapter()


def make_piece():
    adapter_piece = make_adapter_piece()
    return htypes.list.view(mosaic.put(adapter_piece))


def test_list():
    ctx = Context()
    piece = make_piece()
    model = (
        htypes.list_tests.item(1, "First"),
        htypes.list_tests.item(2, "Second"),
        )
    state = None
    app = QtWidgets.QApplication()
    try:
        view = list.ListView.from_piece(piece, model, ctx)
        view.set_controller_hook(Mock())
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        # assert state
    finally:
        app.shutdown()
