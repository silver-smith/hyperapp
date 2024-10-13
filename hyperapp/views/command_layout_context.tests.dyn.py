from unittest.mock import Mock

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.context import Context
from .fixtures import qapp_fixtures
from .tested.code import command_layout_context


@mark.fixture
def view_creg():
    return Mock()


def open_command_layout_context(data_to_ref, view_creg, piece):
    ctx = Context()
    command_d = htypes.command_layout_context_tests.sample_command_d()
    current_item = htypes.model_commands.item(
        command_d=data_to_ref(command_d),
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


def test_open_model_command_layout_context(data_to_ref, view_creg):
    model = htypes.command_layout_context_tests.sample_model()
    model_state = htypes.command_layout_context_tests.sample_model_state()
    piece = htypes.model_commands.view(
        model=mosaic.put(model),
        model_state=mosaic.put(model_state)
        )
    open_command_layout_context(data_to_ref, view_creg, piece)


def test_open_global_command_layout_context(data_to_ref, view_creg):
    piece = htypes.global_commands.view()
    open_command_layout_context(data_to_ref, view_creg, piece)


def test_view(data_to_ref, qapp, view_creg):
    model = htypes.command_layout_context_tests.sample_model()
    model_state = htypes.command_layout_context_tests.sample_model_state()
    command_d = htypes.command_layout_context_tests.sample_command_d()
    base_piece = htypes.label.view("Sample label")
    piece = htypes.command_layout_context.view(
        base=mosaic.put(base_piece),
        model=mosaic.put(model),
        ui_command_d=data_to_ref(command_d),
        )
    base_state = htypes.label.state()
    state = htypes.command_layout_context.state(
        base=mosaic.put(base_state),
        )
    ctx = Context(
        lcs=Mock(),
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


def _test_set_external_layout():
    _view_creg_mock.invite = real_view_creg.invite  # Used to resolve base view.
    sample_ui_command = _make_sample_external_ui_command()
    lcs = Mock()
    ctx = Context(
        lcs=lcs,
        )
    model = htypes.command_layout_context_tests.sample_model()
    base_piece = htypes.label.view("Sample label")
    piece = htypes.command_layout_context.view(
        base=mosaic.put(base_piece),
        model=mosaic.put(model),
        ui_command=mosaic.put(sample_ui_command),
        )
    view = command_layout_context.CommandLayoutContextView.from_piece(piece, ctx)
    view._set_layout(htypes.label.view("Sample label layout"))
    lcs.set.assert_called_once()


def _test_set_usual_layout():
    _view_creg_mock.invite = real_view_creg.invite  # Used to resolve base view.
    sample_ui_command = _make_sample_ui_command()
    lcs = Mock()
    ctx = Context(
        lcs=lcs,
        )
    model = htypes.command_layout_context_tests.sample_model()
    base_piece = htypes.label.view("Sample label")
    piece = htypes.command_layout_context.view(
        base=mosaic.put(base_piece),
        model=mosaic.put(model),
        ui_command=mosaic.put(sample_ui_command),
        )
    view = command_layout_context.CommandLayoutContextView.from_piece(piece, ctx)
    lcs.get.return_value = htypes.ui.ui_model_command_list([
        mosaic.put(sample_ui_command),
        ])
    view._set_layout(htypes.label.view("Sample label layout"))
    lcs.set.assert_called_once()
