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
        view = tabs.TabsCtl.from_piece(piece)
        widget = view.construct_widget(piece, state, ctx)
        state = view.widget_state(piece, widget)
        assert state
    finally:
        app.shutdown()


def test_duplicate():
    ctx = Context(command_hub=CommandHub())
    piece = make_inner_layout()
    state = make_inner_state()
    app = QtWidgets.QApplication()
    try:
        view = tabs.TabsCtl.from_piece(piece)
        widget = view.construct_widget(piece, state, ctx)
        piece_diff, state_diff = tabs.duplicate(piece, state)
        new_piece, new_state = view.apply(ctx, piece, widget, piece_diff, state_diff)
        assert len(new_piece.tabs) == 2
        assert new_piece.tabs[0] == piece.tabs[0]
        assert new_piece.tabs[0] == new_piece.tabs[1]
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
        view = tabs.TabsCtl.from_piece(outer_piece)
        widget = view.construct_widget(outer_piece, outer_state, ctx)
        inner_piece_diff, inner_state_diff = tabs.duplicate(inner_piece, inner_state)
        outer_piece_diff, outer_state_diff = view.wrapper(
            widget, (inner_piece_diff, inner_state_diff),
            )
        new_outer_piece, new_outer_state = view.apply(
            ctx, outer_piece, widget, outer_piece_diff, outer_state_diff)
        assert len(new_outer_piece.tabs) == 1
        new_inner_piece = web.summon(new_outer_piece.tabs[0].ctl)
        assert len(new_inner_piece.tabs) == 2
        assert new_inner_piece.tabs[0] == inner_piece.tabs[0]
        assert new_inner_piece.tabs[0] == new_inner_piece.tabs[1]
    finally:
        app.shutdown()
