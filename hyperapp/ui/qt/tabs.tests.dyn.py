from unittest.mock import Mock

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.list_diff import ListDiff
from .code.context import Context
from .code.view import Diff
from .tested.code import tabs


def make_inner_piece():
    adapter = htypes.str_adapter.static_str_adapter("Sample text")
    text = htypes.text.readonly_view(mosaic.put(adapter))
    return htypes.tabs.view(
        tabs=(
            htypes.tabs.tab("One", mosaic.put(text)),
            ),
        )


def make_outer_piece(inner_tab_view):
    return htypes.tabs.view(
        tabs=(
            htypes.tabs.tab("Inner", mosaic.put(inner_tab_view)),
            ),
        )


def make_inner_state():
    text_state = htypes.text.state()
    return htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(text_state),),
        )


def make_outer_state(inner_tab_state):
    return htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(inner_tab_state),),
        )


def test_tabs():
    ctx = Context()
    piece = make_inner_piece()
    state = make_inner_state()
    app = QtWidgets.QApplication()
    try:
        view = tabs.TabsView.from_piece(piece, ctx)
        view.set_controller_hook(Mock())
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()


def duplicate(piece, state):
    return Diff(
        piece=ListDiff.Insert(
            idx=state.current_tab + 1,
            item=piece.tabs[state.current_tab],
            ),
        state=ListDiff.Insert(
            idx=state.current_tab + 1,
            item=state.tabs[state.current_tab],
            ),
        )
