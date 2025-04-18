from unittest.mock import Mock

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
def str_adapter():
    return htypes.str_adapter.static_str_adapter()


@mark.fixture
def wiki_adapter():
    return htypes.wiki.adapter()


@mark.fixture
def text_piece(str_adapter):
    return htypes.wiki.text_view(
        adapter=mosaic.put(str_adapter),
        )


@mark.fixture
def wiki_piece(wiki_adapter):
    return htypes.wiki.wiki_view(
        adapter=mosaic.put(wiki_adapter),
        )


@mark.fixture
def state():
    return htypes.wiki.state()


@mark.fixture
def model():
    return htypes.wiki.wiki(
        text="Sample value",
        refs=(),
        )


def test_adapter(ctx, wiki_adapter, model):
    adapter = wiki.StaticWikiAdapter.from_piece(wiki_adapter, model, ctx)
    assert adapter.model == model
    assert adapter.get_text() == model.text


def test_adapter_resource_name(wiki_adapter):
    gen = Mock()
    name = wiki.static_wiki_adapter_resource_name(wiki_adapter, gen)
    assert type(name) is str


def test_text_view(qapp, ctx, text_piece, state):
    model = "Sample wiki text"
    view = wiki.WikiTextView.from_piece(text_piece, model, ctx)
    assert view.piece == text_piece
    widget = view.construct_widget(state, ctx)
    widget_state = view.widget_state(widget)
    assert isinstance(widget_state, htypes.wiki.state)
    assert widget_state == state


def test_wiki_view(qapp, ctx, wiki_piece, state, model):
    view = wiki.WikiView.from_piece(wiki_piece, model, ctx)
    assert view.piece == wiki_piece
    widget = view.construct_widget(state, ctx)
    widget_state = view.widget_state(widget)
    assert isinstance(widget_state, htypes.wiki.state)
    assert widget_state == state


def test_text_view_factory():
    model = "Sample wiki text"
    piece = wiki.wiki_text(model, adapter=None)
    assert isinstance(piece, htypes.wiki.text_view)


def test_wiki_view_factory(model):
    piece = wiki.wiki(model, adapter=None)
    assert isinstance(piece, htypes.wiki.wiki_view)
