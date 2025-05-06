from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import tabs


@mark.fixture
def ctx():
    return Context()


@mark.fixture
def piece():
    label = htypes.label.view("Sample label")
    return htypes.tabs.view(
        tabs=(
            htypes.tabs.tab("One", mosaic.put(label)),
            ),
        )


@mark.fixture
def state():
    label_state = htypes.label.state()
    return htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(label_state),),
        )


def test_tabs(qapp, ctx, piece, state):
    view = tabs.TabsView.from_piece(piece, ctx)
    view.set_controller_hook(Mock())
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert state


def test_tab_list(qapp, ctx, piece, state):
    view = tabs.TabsView.from_piece(piece, ctx)
    view.set_controller_hook(Mock())
    widget = view.construct_widget(state, ctx)
    assert view.piece
    state = view.widget_state(widget)
    assert state
    tab_list = tabs.open_tab_list(view)
    assert tab_list


def test_unwrap(qapp, piece, state, ctx, view_reg):
    view = view_reg.animate(piece, ctx)
    hook = Mock()
    tabs.unwrap(view, state, hook, ctx)
    hook.replace_view.assert_called_once()


def test_wrap():
    inner = htypes.label.view("Inner label")
    piece = tabs.wrap_in_tabs(inner)
    assert isinstance(piece, htypes.tabs.view)
