from unittest.mock import Mock

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import command_layout_context


@mark.fixture
def view_creg():
    return Mock()


@mark.fixture
def open_command_layout_context(data_to_ref, view_creg, piece):
    ctx = Context()
    current_item = htypes.model_commands.item(
        ui_command_d=data_to_ref(htypes.command_layout_context_tests.sample_command_d()),
        model_command_d=data_to_ref(htypes.command_layout_context_tests.sample_model_command_d()),
        name="<unused>",
        groups="<unused>",
        repr="<unused>",
        )
    navigator = Mock()
    navigator.view.piece = htypes.label.view("Sample view")
    navigator.state = htypes.label.state()
    command_layout_context.open_command_layout_context(piece, current_item, navigator, ctx)
    view_creg.animate.assert_called_once()
    navigator.hook.replace_view.assert_called_once()


def test_open_model_command_layout_context(open_command_layout_context):
    model = htypes.command_layout_context_tests.sample_model()
    model_state = htypes.command_layout_context_tests.sample_model_state()
    piece = htypes.model_commands.view(
        model=mosaic.put(model),
        model_state=mosaic.put(model_state)
        )
    open_command_layout_context(piece)


def test_open_global_command_layout_context(open_command_layout_context):
    piece = htypes.global_commands.view()
    open_command_layout_context(piece)


@mark.fixture
def base_piece():
    return htypes.label.view("Sample label")


@mark.fixture
def piece(data_to_ref, base_piece):
    model_t = htypes.command_layout_context_tests.sample_model
    return htypes.command_layout_context.view(
        base=mosaic.put(base_piece),
        model_t=pyobj_creg.actor_to_ref(model_t),
        ui_command_d=data_to_ref(htypes.command_layout_context_tests.sample_command_d()),
        model_command_d=data_to_ref(htypes.command_layout_context_tests.sample_model_command_d()),
        )


@mark.fixture
def ctx():
    return Context(
        lcs=Mock(),
        )


def test_view(qapp, view_creg, base_piece, piece, ctx):
    base_state = htypes.label.state()
    state = htypes.command_layout_context.state(
        base=mosaic.put(base_state),
        )

    base_view = Mock()
    base_view.piece = base_piece
    base_view.widget_state.return_value = base_state
    base_view.construct_widget.return_value = QtWidgets.QLabel()
    view_creg.invite.return_value = base_view

    view = command_layout_context.CommandLayoutContextView.from_piece(piece, ctx)
    assert isinstance(view.piece, htypes.command_layout_context.view)
    widget = view.construct_widget(state, ctx)
    state = view.widget_state(widget)
    assert isinstance(state, htypes.command_layout_context.state)


def test_set_layout(piece, ctx):
    view = command_layout_context.CommandLayoutContextView.from_piece(piece, ctx)
    children_ctx = view.children_context(ctx)
    children_ctx.set_layout(htypes.label.view("Sample label layout"))
    ctx.lcs.set.assert_called_once()
