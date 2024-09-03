from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import window


@mark.fixture
def piece():
    label = htypes.label.view("Sample label")
    tabs_piece = htypes.tabs.view(
        tabs=(htypes.tabs.tab("One", mosaic.put(label)),),
        )
    return htypes.window.view(
        menu_bar_ref=mosaic.put(htypes.menu_bar.view()),
        central_view_ref=mosaic.put(tabs_piece),
        )


@mark.fixture
def state():
    label_state = htypes.label.state()
    tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(label_state),),
        )
    return htypes.window.state(
        menu_bar_state=mosaic.put(htypes.menu_bar.state()),
        central_view_state=mosaic.put(tabs_state),
        size=htypes.window.size(100, 100),
        pos=htypes.window.pos(10, 10),
        )


def test_construct_widget(qapp, piece, state):
    ctx = Context()
    view = window.WindowView.from_piece(piece, ctx)
    assert view.piece
    widget = view.construct_widget(state, ctx)
    state = view.widget_state(widget)
    assert state
