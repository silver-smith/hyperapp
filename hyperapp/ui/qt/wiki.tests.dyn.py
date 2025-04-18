from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import wiki


@mark.fixture
def ctx():
    return Context()


@mark.fixture
def adapter():
    return htypes.str_adapter.static_str_adapter()


@mark.fixture
def piece(adapter):
    return htypes.wiki.view(
        adapter=mosaic.put(adapter),
        )


@mark.fixture
def state():
    return htypes.wiki.state()


def test_view(qapp, ctx, piece, state):
    model = """
        Sample wiki text
        This is ref#[1].
        And this is ref#[2].
    """
    view = wiki.WikiView.from_piece(piece, model, ctx)
    assert view.piece == piece
    widget = view.construct_widget(state, ctx)
    widget_state = view.widget_state(widget)
    assert isinstance(widget_state, htypes.wiki.state)
    assert widget_state == state


def test_view_factory():
    model = "Sample wiki text"
    piece = wiki.wiki(model, adapter=None)
    assert isinstance(piece, htypes.wiki.view)
