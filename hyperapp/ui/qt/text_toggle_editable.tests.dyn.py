from unittest.mock import Mock

from PySide6 import QtWidgets

from . import htypes
from .services import (
    model_view_creg,
    mosaic,
    )
from .code.context import Context
from .tested.code import text_toggle_editable


def readonly_view():
    adapter = htypes.str_adapter.static_str_adapter()
    return htypes.text.readonly_view(mosaic.put(adapter))


def edit_view():
    adapter = htypes.str_adapter.static_str_adapter()
    return htypes.text.edit_view(mosaic.put(adapter))


def make_state():
    return htypes.text.state()


def test_readonly_to_edit():
    ctx = Context()
    view_piece = readonly_view()
    state = make_state()
    model = "Sample text"
    app = QtWidgets.QApplication()
    try:
        view = model_view_creg.animate(view_piece, model, ctx)
        hook = Mock()
        text_toggle_editable.toggle_editable(model, view, hook, ctx)
        hook.replace_view.assert_called_once()
    finally:
        app.shutdown()


def test_edit_to_readonly():
    ctx = Context()
    view_piece = edit_view()
    state = make_state()
    model = "Sample text"
    app = QtWidgets.QApplication()
    try:
        view = model_view_creg.animate(view_piece, model, ctx)
        hook = Mock()
        text_toggle_editable.toggle_editable(model, view, hook, ctx)
        hook.replace_view.assert_called_once()
    finally:
        app.shutdown()
