from PySide6 import QtWidgets

from . import htypes
from .tested.code import tabs
from .services import (
    mosaic,
    web,
    )
from .code.context import Context
from .code.command_hub import CommandHub


def make_inner_layout():
    adapter_layout = htypes.str_adapter.static_str_adapter("Sample text")
    tab_layout = htypes.text.view_layout(mosaic.put(adapter_layout))
    return htypes.tabs.layout(
        tabs=[
            htypes.tabs.tab("One", mosaic.put(tab_layout))],
        )


def make_outer_layout(tab_layout):
    return htypes.tabs.layout(
        tabs=[
            htypes.tabs.tab("Inner", mosaic.put(tab_layout))],
        )


def make_inner_state():
    tab_state = htypes.text.state()
    return htypes.tabs.state(
        current_tab=0,
        tabs=[mosaic.put(tab_state)],
        )


def make_outer_state(tab_state):
    return htypes.tabs.state(
        current_tab=0,
        tabs=[mosaic.put(tab_state)],
        )


def test_tabs():
    ctx = Context(command_hub=CommandHub())
    piece = make_inner_layout()
    state = make_inner_state()
    app = QtWidgets.QApplication()
    try:
        view = tabs.TabsView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()


def test_duplicate():
    ctx = Context(command_hub=CommandHub())
    piece = make_inner_layout()
    state = make_inner_state()
    app = QtWidgets.QApplication()
    try:
        view = tabs.TabsView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        piece_diff, state_diff = tabs.duplicate(piece, state)
        new_state, replace = view.apply(ctx, widget, piece_diff, state_diff)
        assert len(view.piece.tabs) == 2
        assert view.piece.tabs[0] == piece.tabs[0]
        assert view.piece.tabs[0] == view.piece.tabs[1]
    finally:
        app.shutdown()


def test_close():
    adapter_layout = htypes.str_adapter.static_str_adapter("Sample text")
    text_layout = htypes.text.view_layout(mosaic.put(adapter_layout))
    piece = htypes.tabs.layout(
        tabs=[
            htypes.tabs.tab("One", mosaic.put(text_layout)),
            htypes.tabs.tab("Two", mosaic.put(text_layout)),
            ],
        )
    text_state = htypes.text.state()
    state = htypes.tabs.state(
        current_tab=0,
        tabs=[
            mosaic.put(text_state),
            mosaic.put(text_state),
            ],
        )
    ctx = Context(command_hub=CommandHub())
    app = QtWidgets.QApplication()
    try:
        view = tabs.TabsView.from_piece(piece)
        widget = view.construct_widget(state, ctx)
        piece_diff, state_diff = tabs.close_tab(piece, state)
        new_state, replace = view.apply(ctx, widget, piece_diff, state_diff)
        assert len(view.piece.tabs) == 1
        assert view.piece.tabs[0] == piece.tabs[1]
    finally:
        app.shutdown()


def test_modify():
    ctx = Context(command_hub=CommandHub())
    inner_piece = make_inner_layout()
    outer_piece = make_outer_layout(inner_piece)
    inner_state = make_inner_state()
    outer_state = make_outer_state(inner_state)
    app = QtWidgets.QApplication()
    try:
        view = tabs.TabsView.from_piece(outer_piece)
        widget = view.construct_widget(outer_state, ctx)
        inner_piece_diff, inner_state_diff = tabs.duplicate(inner_piece, inner_state)
        outer_piece_diff, outer_state_diff = view.wrapper(
            widget, (inner_piece_diff, inner_state_diff),
            )
        new_outer_state, replace = view.apply(
            ctx, widget, outer_piece_diff, outer_state_diff)
        assert len(view.piece.tabs) == 1
        new_inner_piece = web.summon(view.piece.tabs[0].ctl)
        assert len(new_inner_piece.tabs) == 2
        assert new_inner_piece.tabs[0] == inner_piece.tabs[0]
        assert new_inner_piece.tabs[0] == new_inner_piece.tabs[1]
    finally:
        app.shutdown()
