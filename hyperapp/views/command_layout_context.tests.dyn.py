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
from .services import view_creg as real_view_creg
from .code.context import Context
from .tested.code import command_layout_context


_view_creg_mock = Mock()


@mark.service
def view_creg():
    return _view_creg_mock


def _sample_command_fn(piece, ctx):
    return "Sample result"


def _make_sample_external_ui_command():
    d_res = data_to_res(htypes.command_layout_context_tests.sample_d())
    model_impl = htypes.ui.model_command_impl(
        function=fn_to_ref(_sample_command_fn),
        params=('piece', 'ctx'),
        )
    ui_impl = htypes.ui.external_ui_model_command_impl(
        model_command_impl=mosaic.put(model_impl),
        layout=None,
        )
    return htypes.ui.command(
        d=mosaic.put(d_res),
        impl=mosaic.put(ui_impl),
        )


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


def test_open_command_layout_context():
    sample_ui_command = _make_sample_external_ui_command()
    ctx = Context()
    model = htypes.command_layout_context_tests.sample_model()
    model_state = htypes.command_layout_context_tests.sample_model_state()
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
    navigator.view.piece = htypes.label.view("Sample view")
    navigator.state = htypes.label.state()
    command_layout_context.open_command_layout_context(piece, current_item, navigator, ctx)
    _view_creg_mock.animate.assert_called_once()
    navigator.hook.replace_view.assert_called_once()


def test_view():
    _view_creg_mock.invite = real_view_creg.invite  # Used to resolve base view.
    sample_ui_command = _make_sample_external_ui_command()
    ctx = Context(
        lcs=Mock(),
        )
    model = htypes.command_layout_context_tests.sample_model()
    base_piece = htypes.label.view("Sample label")
    piece = htypes.command_layout_context.view(
        base=mosaic.put(base_piece),
        model=mosaic.put(model),
        ui_command=mosaic.put(sample_ui_command),
        )
    base_state = htypes.label.state()
    state = htypes.command_layout_context.state(
        base=mosaic.put(base_state),
        )
    app = QtWidgets.QApplication()
    try:
        view = command_layout_context.CommandLayoutContextView.from_piece(piece, ctx)
        widget = view.construct_widget(state, ctx)
        assert view.piece
        state = view.widget_state(widget)
        assert state
    finally:
        app.shutdown()


def test_set_external_layout():
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


def test_set_usual_layout():
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
