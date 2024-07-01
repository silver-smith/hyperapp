from unittest.mock import Mock

from PySide6 import QtWidgets

from . import htypes
from .services import (
    data_to_res,
    fn_to_ref,
    mark,
    mosaic,
    web,
    )
from .services import model_view_creg as real_model_view_creg
from .code.context import Context
from .tested.code import rename_command


_model_view_creg_mock = Mock()


@mark.service
def model_view_creg():
    return _model_view_creg_mock


def _sample_command_fn(piece, ctx):
    return "Sample result"


def _make_sample_ui_command():
    d_res = data_to_res(htypes.command_layout_context_tests.sample_d())
    model_impl = htypes.ui.model_command_impl(
        function=fn_to_ref(_sample_command_fn),
        params=('piece', 'ctx'),
        )
    ui_impl = htypes.ui.ui_model_command_impl(
        model_command_impl=mosaic.put(model_impl),
        layout=None,
        )
    return htypes.ui.command(
        d=mosaic.put(d_res),
        impl=mosaic.put(ui_impl),
        )


def test_view():
    _model_view_creg_mock.invite = real_model_view_creg.invite  # Used to resolve base view.
    sample_ui_command = _make_sample_ui_command()
    ctx = Context(
        lcs=Mock(),
        )
    model = "Sample command name"
    adapter = htypes.str_adapter.static_str_adapter()
    text_view = htypes.text.edit_view(
        adapter=mosaic.put(adapter),
        )
    piece = htypes.rename_command.view(
        base=mosaic.put(text_view),
        ui_command=mosaic.put(sample_ui_command),
        )
    text_state = htypes.text.state()
    state = htypes.rename_command.state(
        base=mosaic.put(text_state),
        )
    app = QtWidgets.QApplication()
    try:
        view = rename_command.RenameCommandContextView.from_piece(piece, model, ctx)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()


def test_rename_command():
    sample_ui_command = _make_sample_ui_command()
    ctx = Context()
    model = htypes.rename_command_tests.sample_model()
    model_state = htypes.rename_command_tests.sample_model_state()
    piece = htypes.model_commands.model_commands(
        model=mosaic.put(model),
        model_state=mosaic.put(model_state)
        )
    current_item = htypes.model_commands.item(
        command=mosaic.put(sample_ui_command),
        name="<unused>",
        impl="<unused>",
        )
    navigator = Mock()
    rename_command.rename_command(piece, current_item, navigator, ctx)
    _model_view_creg_mock.animate.assert_called_once()
    navigator.view.open.assert_called_once()
