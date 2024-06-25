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
from .tested.services import ui_model_command_factory, set_ui_model_command


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


def test_ui_model_command_factory():
    ctx = Context()
    piece = "Sample piece"
    commands = ui_model_command_factory(piece, ctx)
    assert commands


def _sample_fn(piece):
    pass


class PhonyAssociationRegistry:

    def __getitem__(self, key):
        return htypes.ui.command_properties(
            is_global=False,
            uses_state=False,
            remotable=False,
            )


@mark.service
def association_reg():
    return PhonyAssociationRegistry()


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
        )
    impl = ui_model_command.ui_model_command_impl_from_piece(piece, ctx)
    assert impl
    assert impl.properties


def test_set_ui_model_command():
    lcs = Mock()
    model = "Sample model"
    command = Mock()
    command.d = data_to_ref(htypes.ui_model_command_tests.sample_d())
    set_ui_model_command(lcs, model, command)
    lcs.set.assert_called_once()
