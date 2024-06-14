import asyncio
from unittest.mock import Mock

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    )
from .code.context import Context
from .tested.code import navigator


def _wrapper(diff):
    return diff


def make_piece():
    adapter_piece = htypes.str_adapter.static_str_adapter()
    text_piece = htypes.text.readonly_view(mosaic.put(adapter_piece))
    prev_rec = htypes.navigator.history_rec(
        view=mosaic.put(text_piece),
        model=mosaic.put("Sample piece"),
        state=mosaic.put(htypes.text.state()),
        prev=None,
        next=None,
        )
    next_rec = htypes.navigator.history_rec(
        view=mosaic.put(text_piece),
        model=mosaic.put("Sample piece"),
        state=mosaic.put(htypes.text.state()),
        prev=None,
        next=None,
        )
    piece = htypes.navigator.view(
        current_view=mosaic.put(text_piece),
        current_model=mosaic.put("Sample piece"),
        prev=mosaic.put(prev_rec),
        next=mosaic.put(next_rec),
        )
    return piece


def make_state():
    return htypes.text.state()


def test_navigator():
    piece = make_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        ctx = Context(lcs=None)
        view = navigator.NavigatorView.from_piece(piece, ctx)
        view.set_controller_hook(Mock())
        widget = view.construct_widget(state, ctx)
        assert view.piece
        assert view.widget_state(widget) == htypes.text.state()
    finally:
        app.shutdown()


def test_go_back_command():
    piece = make_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        ctx = Context(lcs=None)
        view = navigator.NavigatorView.from_piece(piece, ctx)
        view.set_controller_hook(Mock())
        widget = view.construct_widget(state, ctx)
        navigator.go_back(view, state, widget)
    finally:
        app.shutdown()


def test_go_forward_command():
    piece = make_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        ctx = Context(lcs=None)
        view = navigator.NavigatorView.from_piece(piece, ctx)
        view.set_controller_hook(Mock())
        widget = view.construct_widget(state, ctx)
        navigator.go_forward(view, state, widget)
    finally:
        app.shutdown()
