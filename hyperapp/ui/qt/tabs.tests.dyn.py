from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.list_diff import ListDiff
from .code.context import Context
from .code.command_hub import CommandHub
from .code.view import Diff
from .tested.code import tabs


def make_inner_piece():
    adapter = htypes.str_adapter.static_str_adapter("Sample text")
    text = htypes.text.view_layout(mosaic.put(adapter))
    return htypes.tabs.view(
        tabs=[
            htypes.tabs.tab("One", mosaic.put(text))],
        )


def make_outer_piece(inner_tab_view):
    return htypes.tabs.view(
        tabs=[
            htypes.tabs.tab("Inner", mosaic.put(inner_tab_view))],
        )


def make_inner_state():
    text_state = htypes.text.state()
    return htypes.tabs.state(
        current_tab=0,
        tabs=[mosaic.put(text_state)],
        )


def make_outer_state(inner_tab_state):
    return htypes.tabs.state(
        current_tab=0,
        tabs=[mosaic.put(inner_tab_state)],
        )


def test_tabs():
    ctx = Context(command_hub=CommandHub())
    piece = make_inner_piece()
    state = make_inner_state()
    app = QtWidgets.QApplication()
    try:
        view = tabs.TabsView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()


def duplicate(layout, state):
    return Diff(
        piece=ListDiff.Insert(
            idx=state.current_tab + 1,
            item=layout.tabs[state.current_tab],
            ),
        state=ListDiff.Insert(
            idx=state.current_tab + 1,
            item=state.tabs[state.current_tab],
            ),
        )


def test_duplicate():
    ctx = Context(command_hub=CommandHub())
    piece = make_inner_piece()
    state = make_inner_state()
    app = QtWidgets.QApplication()
    try:
        view = tabs.TabsView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        diff = duplicate(piece, state)
        replace_widget = view.apply(ctx, widget, diff)
        assert len(view.piece.tabs) == 2
        assert view.piece.tabs[0] == piece.tabs[0]
        assert view.piece.tabs[0] == view.piece.tabs[1]
    finally:
        app.shutdown()
