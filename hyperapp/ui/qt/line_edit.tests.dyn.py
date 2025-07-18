from unittest.mock import Mock

from hyperapp.boot.htypes import TOptional

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import line_edit



@mark.fixture
def ctx():
    return Context()


@mark.fixture
def adapter():
    accessor = htypes.accessor.model_accessor()
    cvt = htypes.type_convertor.noop_convertor()
    return htypes.value_adapter.value_adapter(
        accessor=mosaic.put(accessor),
        convertor=mosaic.put(cvt),
        )


@mark.fixture
def view_piece(adapter):
    return htypes.line_edit.readonly_view(
        adapter=mosaic.put(adapter),
        )


@mark.fixture
def edit_piece(adapter):
    return htypes.line_edit.edit_view(
        adapter=mosaic.put(adapter),
        )


@mark.fixture
def state():
    return htypes.line_edit.state('')


def test_edit_view(qapp, ctx, edit_piece, state):
    model = "Sample text"
    view = line_edit.EditLineView.from_piece(edit_piece, model, ctx)
    widget = view.construct_widget(state, ctx)
    assert view.piece == edit_piece
    widget_state = view.widget_state(widget)
    assert widget_state == state


def test_readonly_view(qapp, ctx, view_piece, state):
    model = "Sample text"
    view = line_edit.ViewLineView.from_piece(view_piece, model, ctx)
    widget = view.construct_widget(state, ctx)
    assert view.piece == view_piece
    widget_state = view.widget_state(widget)
    assert widget_state == state


@mark.fixture
def accessor():
    return htypes.accessor.model_accessor()


def test_edit_factory(accessor):
    piece = line_edit.line_edit(htypes.builtin.string, accessor)
    assert piece


def test_opt_edit_factory(accessor):
    piece = line_edit.line_edit(TOptional(htypes.builtin.string), accessor)
    assert piece


def test_int_edit_factory(accessor):
    piece = line_edit.line_edit(htypes.builtin.int, accessor)
    assert piece


def test_view_factory(accessor):
    piece = line_edit.line_view(htypes.builtin.string, accessor)
    assert piece


def test_opt_view_factory(accessor):
    piece = line_edit.line_view(TOptional(htypes.builtin.string), accessor)
    assert piece


def test_int_view_factory(accessor):
    piece = line_edit.line_view(htypes.builtin.int, accessor)
    assert piece


def test_line_edit_resource_name(edit_piece):
    gen = Mock()
    gen.assigned_name.return_value = 'some-adapter'
    name = line_edit.line_edit_resource_name(edit_piece, gen)
    assert type(name) is str


def test_line_view_resource_name(view_piece):
    gen = Mock()
    gen.assigned_name.return_value = 'some-adapter'
    name = line_edit.line_view_resource_name(view_piece, gen)
    assert type(name) is str
