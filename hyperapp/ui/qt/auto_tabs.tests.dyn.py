from unittest.mock import Mock

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.context import Context
from .tested.code import auto_tabs


def make_piece():
    label = htypes.label.view("Sample label")
    return htypes.auto_tabs.view(
        tabs=(mosaic.put(label),),
        )


def make_state():
    label_state = htypes.label.state()
    return htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(label_state),),
        )


def test_tabs():
    ctx = Context()
    piece = make_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        view = auto_tabs.AutoTabsView.from_piece(piece, ctx)
        view.set_controller_hook(Mock())
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()


def test_duplicate():
    ctx = Context()
    piece = make_piece()
    state = make_state()
    app = QtWidgets.QApplication()
    try:
        view = auto_tabs.AutoTabsView.from_piece(piece, ctx)
        view.set_controller_hook(Mock())
        widget = view.construct_widget(state, ctx)
        auto_tabs.duplicate_tab(ctx, view, widget, state)
        assert len(view.piece.tabs) == 2
        assert view.piece.tabs[0] == piece.tabs[0]
        assert view.piece.tabs[0] == view.piece.tabs[1]
    finally:
        app.shutdown()


def test_close():
    label = htypes.label.view("Sample label")
    piece = htypes.auto_tabs.view(
        tabs=(
            mosaic.put(label),
            mosaic.put(label),
            ),
        )
    label_state = htypes.label.state()
    state = htypes.tabs.state(
        current_tab=0,
        tabs=(
            mosaic.put(label_state),
            mosaic.put(label_state),
            ),
        )
    ctx = Context()
    app = QtWidgets.QApplication()
    try:
        view = auto_tabs.AutoTabsView.from_piece(piece, ctx)
        view.set_controller_hook(Mock())
        widget = view.construct_widget(state, ctx)
        auto_tabs.close_tab(view, widget, state)
        assert len(view.piece.tabs) == 1
        assert view.piece.tabs[0] == piece.tabs[1]
    finally:
        app.shutdown()
