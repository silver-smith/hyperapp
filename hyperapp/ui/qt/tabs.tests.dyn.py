from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.list_diff import ListDiff
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import tabs


def make_inner_piece():
    label = htypes.label.view("Sample label")
    return htypes.tabs.view(
        tabs=(
            htypes.tabs.tab("One", mosaic.put(label)),
            ),
        )


def make_outer_piece(inner_tab_view):
    return htypes.tabs.view(
        tabs=(
            htypes.tabs.tab("Inner", mosaic.put(inner_tab_view)),
            ),
        )


def make_inner_state():
    label_state = htypes.label.state()
    return htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(label_state),),
        )


def make_outer_state(inner_tab_state):
    return htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(inner_tab_state),),
        )


def test_tabs(qapp):
    ctx = Context()
    piece = make_inner_piece()
    state = make_inner_state()

    view = tabs.TabsView.from_piece(piece, ctx)
    view.set_controller_hook(Mock())
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert state


def test_tab_list(qapp):
    ctx = Context()
    piece = make_inner_piece()
    state = make_inner_state()

    view = tabs.TabsView.from_piece(piece, ctx)
    view.set_controller_hook(Mock())
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert state
    tab_list = tabs.open_tab_list(view)
    assert tab_list
