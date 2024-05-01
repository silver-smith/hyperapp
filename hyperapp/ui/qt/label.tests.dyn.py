from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    )
from .code.context import Context
from .tested.code import label


def test_label():
    ctx = Context()
    piece = htypes.label.view("Sample label")
    state = htypes.label.state()
    app = QtWidgets.QApplication()
    try:
        view = label.LabelView.from_piece(piece, ctx)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()
