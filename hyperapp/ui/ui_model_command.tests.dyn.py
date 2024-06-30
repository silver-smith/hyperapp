from unittest.mock import Mock

from . import htypes
from .services import (
    data_to_ref,
    fn_to_ref,
    mark,
    mosaic,
    )
from .code.context import Context
from .tested.code import ui_model_command
from .tested.services import (
    list_ui_model_commands,
    set_ui_model_commands,
    set_ui_model_command_layout,
    )


def _phony_fn(piece, ctx):
    return "Sample result"


def _make_sample_command():
    d_res_ref = data_to_ref(htypes.ui_model_command_tests.sample_d())
    impl = htypes.ui.model_command_impl(
        function=fn_to_ref(_phony_fn),
        params=('piece', 'ctx'),
        )
    return htypes.ui.command(
        d=d_res_ref,
        impl=mosaic.put(impl),
        )


@mark.service
def global_commands():
    def _mock_global_commands():
        return []
    return _mock_global_commands


@mark.service
def model_commands():
    def _mock_model_commands(piece):
        return [_make_sample_command()]
    return _mock_model_commands


@mark.service
def enum_model_commands():
    def _mock_enum_model_commands(piece, ctx):
        return []
    return _mock_enum_model_commands


def test_list_ui_model_commands():
    lcs = Mock()
    lcs.get.return_value = None
    ctx = Context()
    piece = "Sample piece"
    commands = list_ui_model_commands(lcs, piece, ctx)
    assert commands


def _sample_fn(piece):
    pass


def test_command_impl_from_piece():
    ctx = Context(
        lcs=None,
        navigator=None,
        )
    model_impl = htypes.ui.model_command_impl(
        function=fn_to_ref(_sample_fn),
        params=('piece',),
        )
    piece = htypes.ui.ui_model_command_impl(
        model_command_impl=mosaic.put(model_impl),
        layout=None,
        )
    impl = ui_model_command.ui_model_command_impl_from_piece(piece, ctx)
    assert impl
    assert impl.properties


def test_set_ui_model_command_layout():
    lcs = Mock()
    command_d = data_to_ref(htypes.ui_model_command_tests.sample_d())
    layout = None
    set_ui_model_command_layout(lcs, command_d, layout)
    lcs.set.assert_called_once()


def test_set_ui_model_commands():
    lcs = Mock()
    model = "Sample model"
    commands = ["Sample 1", "Sample 2"]
    set_ui_model_commands(lcs, model, commands)
    lcs.set.assert_called_once()
