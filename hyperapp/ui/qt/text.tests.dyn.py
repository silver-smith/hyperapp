from PySide6 import QtWidgets

from . import htypes
from .tested.code import text
from .services import (
    mosaic,
    )
from .code.context import Context


def make_adapter_layout():
    return htypes.str_adapter.static_str_adapter("Sample text")


def make_view_layout():
    adapter_layout = make_adapter_layout()
    return htypes.text.view_layout(mosaic.put(adapter_layout))


def make_edit_layout():
    adapter_layout = make_adapter_layout()
    return htypes.text.edit_layout(mosaic.put(adapter_layout))


def make_state():
    return htypes.text.state()


def test_view_text():
    ctx = Context()
    layout = make_view_layout()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        ctl = text.ViewTextCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx)
        state = ctl.widget_state(widget)
        assert state
    finally:
        app.shutdown()


def test_edit_text():
    ctx = Context()
    layout = make_edit_layout()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        ctl = text.EditTextCtl.from_piece(layout)
        widget = ctl.construct_widget(state, ctx)
        state = ctl.widget_state(widget)
        assert state
    finally:
        app.shutdown()
