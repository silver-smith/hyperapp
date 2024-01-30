import asyncio

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    )
from .code.context import Context
from .code.command_hub import CommandHub
from .tested.code import navigator


def _wrapper(diffs):
    return diffs


def make_piece():
    adapter_piece = htypes.str_adapter.static_str_adapter("Sample text")
    text_piece = htypes.text.view_layout(mosaic.put(adapter_piece))
    prev_piece = htypes.navigator.layout(
        current_layout=mosaic.put(text_piece),
        current_model=mosaic.put("Sample piece"),
        commands=[],
        prev=None,
        next=None,
        )
    next_piece = htypes.navigator.layout(
        current_layout=mosaic.put(text_piece),
        current_model=mosaic.put("Sample piece"),
        commands=[],
        prev=None,
        next=None,
        )
    piece = htypes.navigator.layout(
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
        view = navigator.NavigatorCtl.from_piece(piece)
        widget = view.construct_widget(piece, state, ctx)
        state = view.widget_state(piece, widget)
        assert state

        diffs = view._wrapper("Sample text")
        piece_diff, state_diff = diffs
        assert len(diffs) == 2
        view.apply(ctx, piece, widget, piece_diff, state_diff)        
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
