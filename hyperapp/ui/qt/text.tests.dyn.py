from PySide6 import QtWidgets

from . import htypes
from .tested.code import text
from .services import (
    mosaic,
    )
from .code.context import Context


def make_layout():
    return htypes.text.layout()


def make_state():
    return htypes.text.state(
        text="Sample text",
        )


def test_text():
    ctx = Context()
    layout = make_layout()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        ctl = text.TextCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx)
        state = ctl.widget_state(widget)
        assert state
    finally:
        app.shutdown()
