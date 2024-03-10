import asyncio

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    )
from .code.context import Context
from .code.command_hub import CommandHub
from .tested.code import navigator


def _wrapper(diff):
    return diff


def make_piece():
    adapter_piece = htypes.str_adapter.static_str_adapter("Sample text")
    text_piece = htypes.text.view_layout(mosaic.put(adapter_piece))
    prev_piece = htypes.navigator.view(
        current_layout=mosaic.put(text_piece),
        current_model=mosaic.put("Sample piece"),
        commands=[],
        prev=None,
        next=None,
        )
    next_piece = htypes.navigator.view(
        current_layout=mosaic.put(text_piece),
        current_model=mosaic.put("Sample piece"),
        commands=[],
        prev=None,
        next=None,
        )
    piece = htypes.navigator.view(
        current_layout=mosaic.put(text_piece),
        current_model=mosaic.put("Sample piece"),
        commands=[],
        prev=mosaic.put(prev_piece),
        next=mosaic.put(next_piece),
        )
    return piece


def make_state():
    tab_state = htypes.text.state()
    state = htypes.navigator.state(
        current_state=mosaic.put(tab_state),
        prev=None,
        next=None,
        )
    return state


def test_navigator():
    piece = make_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        ctx = Context(command_hub=CommandHub())
        view = navigator.NavigatorView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        state = view.widget_state(widget)
        assert state

        diff = view._model_wrapper("Sample text")
        view.apply(ctx, widget, diff)
    finally:
        app.shutdown()


def test_go_back_command():
    piece = make_piece()
    state = make_state()
    navigator.go_back(piece, state)


def test_go_forward_command():
    piece = make_piece()
    state = make_state()
    navigator.go_forward(piece, state)
