from unittest.mock import AsyncMock, Mock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures
from .fixtures import visualizer_fixtures
from .tested.code import wiki


@mark.fixture
def ctx():
    return Context()


@mark.fixture
def wiki_to_string_convertor():
    return htypes.wiki.wiki_to_string_convertor()


@mark.fixture
def accessor():
    return htypes.accessor.model_accessor()


@mark.fixture
def text_piece(accessor):
    cvt = htypes.type_convertor.noop_convertor()
    adapter = htypes.value_adapter.value_adapter(
        accessor=mosaic.put(accessor),
        convertor=mosaic.put(cvt),
        )
    return htypes.wiki.text_view(
        adapter=mosaic.put(adapter),
        )


@mark.fixture
def wiki_piece(accessor):
    cvt = htypes.type_convertor.noop_convertor()
    adapter = htypes.value_adapter.value_adapter(
        accessor=mosaic.put(accessor),
        convertor=mosaic.put(cvt),
        )
    return htypes.wiki.wiki_view(
        adapter=mosaic.put(adapter),
        )


@mark.fixture
def state():
    return htypes.wiki.state()


@mark.fixture
def sample_ref_target():
    return mosaic.put("Sample target")


@mark.fixture
def model(sample_ref_target):
    return htypes.wiki.wiki(
        text="Sample text",
        refs=(
          htypes.wiki.wiki_ref('a', sample_ref_target),
          ),
        )


def test_convertor(ctx, wiki_to_string_convertor, model):
    cvt = wiki.WikiToTextConvertor.from_piece(wiki_to_string_convertor)
    assert cvt.value_to_view(model) == model.text
    new_value = cvt.view_to_value(model, "New text")
    assert new_value.text == "New text"
    assert new_value.refs == model.refs


def test_convertor_resource_name(wiki_to_string_convertor):
    gen = Mock()
    name = wiki.wiki_convertor_resource_name(wiki_to_string_convertor, gen)
    assert type(name) is str


def test_text_view(qapp, ctx, text_piece, state):
    model = "Sample wiki text"
    view = wiki.WikiTextView.from_piece(text_piece, model, ctx)
    assert view.piece == text_piece
    widget = view.construct_widget(state, ctx)
    widget_state = view.widget_state(widget)
    assert isinstance(widget_state, htypes.wiki.state)
    assert widget_state == state


async def test_wiki_view(qapp, ctx, wiki_piece, state, model):
    ctl_hook = Mock()
    ctl_hook.navigator.view = AsyncMock()
    view = wiki.WikiView.from_piece(wiki_piece, model, ctx)
    view.set_controller_hook(ctl_hook)
    assert view.piece == wiki_piece
    widget = view.construct_widget(state, ctx)
    widget_state = view.widget_state(widget)
    assert isinstance(widget_state, htypes.wiki.state)
    assert widget_state == state

    await view._open_ref('a')
    ctl_hook.navigator.view.open.assert_awaited_once()


def test_view_factory(accessor):
    piece = wiki.wiki_view(accessor)
    assert isinstance(piece, htypes.wiki.text_view)


def test_text_edit_factory(accessor):
    piece = wiki.wiki_text_edit(accessor)
    assert isinstance(piece, htypes.text.edit_view)


def test_text_view_factory(accessor):
    piece = wiki.wiki_text_view(accessor)
    assert isinstance(piece, htypes.text.readonly_view)


def test_wiki_view_factory(accessor):
    piece = wiki.wiki(accessor)
    assert isinstance(piece, htypes.wiki.wiki_view)
