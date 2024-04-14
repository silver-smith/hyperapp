from unittest.mock import Mock

from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from PySide6 import QtWidgets

from . import htypes
from .tested.code import list
from .services import (
    mosaic,
    types,
    )
from .code.context import Context


def make_adapter_piece():
    value = (
        htypes.list_tests.item(1, "First"),
        htypes.list_tests.item(2, "Second"),
        )
    t = deduce_complex_value_type(mosaic, types, value)
    return htypes.list_adapter.static_list_adapter(mosaic.put(value, t))


def make_piece():
    adapter_piece = make_adapter_piece()
    return htypes.list.view(mosaic.put(adapter_piece))


def test_list():
    ctx = Context()
    piece = make_piece()
    state = None
    app = QtWidgets.QApplication()
    try:
        view = list.ListView.from_piece(piece, ctx)
        view.set_controller_hook(Mock())
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        # assert state
    finally:
        app.shutdown()
