from unittest.mock import Mock

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    view_creg,
    )
from .code.context import Context
from .tested.code import local_server_context


def test_local_server_context_view():
    ctx = Context()
    base_piece = htypes.label.view("Sample label")
    piece = htypes.local_server_context.view(
        base=mosaic.put(base_piece),
        )
    base_state = htypes.label.state()
    state = htypes.local_server_context.state(
        base=mosaic.put(base_state),
        )
    app = QtWidgets.QApplication()
    try:
        view = local_server_context.LocalServerContextView.from_piece(piece, ctx)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()


def test_open_local_server_context():
    ctx = Context()
    piece = htypes.label.view("Sample label")
    state = htypes.label.state()
    view = view_creg.animate(piece, ctx)
    hook = Mock()
    result = local_server_context.open_local_server_context(view, state, hook, ctx)
