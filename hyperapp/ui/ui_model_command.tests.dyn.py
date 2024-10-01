from functools import partial
from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .code.model_command import UnboundModelCommand
from .tested.code import ui_model_command


def _sample_fn(model, state, sample_service):
    return f'sample-fn: {state}, {sample_service}'


@mark.config_fixture('global_model_command_reg')
def global_model_command_reg_config(data_to_ref):
    return [
        UnboundModelCommand(
            d=data_to_ref(htypes.ui_model_command_tests.sample_command_d()),
            fn=partial(_sample_fn, sample_service='a-service'),
            ctx_params=('model', 'state'),
            properties=htypes.command.properties(False, False, False),
            ),
        ]


def test_get_ui_model_commands(get_ui_model_commands):
    lcs = Mock()
    lcs.get.return_value = None
    ctx = Context()
    model = htypes.ui_model_command_tests.sample_model()
    commands = get_ui_model_commands(lcs, model, ctx)
    assert commands
    assert isinstance(commands[0], ui_model_command.UnboundUiModelCommand)


# @mark.service
# def global_commands():
#     def _mock_global_commands():
#         return []
#     return _mock_global_commands


# @mark.service
# def model_commands():
#     def _mock_model_commands(piece):
#         return [_make_sample_command()]
#     return _mock_model_commands


# @mark.service
# def enum_model_commands():
#     def _mock_enum_model_commands(piece, ctx):
#         return []
#     return _mock_enum_model_commands


# def test_list_ui_model_commands():
#     lcs = Mock()
#     lcs.get.return_value = None
#     ctx = Context()
#     piece = "Sample piece"
#     commands = list_ui_model_commands(lcs, piece, ctx)
#     assert commands


# def _sample_fn(piece):
#     pass


# def test_command_impl_from_piece():
#     ctx = Context(
#         lcs=None,
#         navigator=None,
#         )
#     model_impl = htypes.ui.model_command_impl(
#         function=fn_to_ref(_sample_fn),
#         params=('piece',),
#         )
#     piece = htypes.ui.ui_model_command_impl(
#         model_command_impl=mosaic.put(model_impl),
#         layout=None,
#         )

#     props_d_res = data_to_res(htypes.ui.command_properties_d())
#     association_reg[props_d_res, model_impl] = htypes.ui.command_properties(
#         is_global=False,
#         uses_state=False,
#         remotable=False,
#         )

#     impl = ui_model_command.ui_model_command_impl_from_piece(piece, ctx)
#     assert impl
#     assert impl.properties


# def test_set_ui_model_command_layout():
#     lcs = Mock()
#     command_d = data_to_ref(htypes.ui_model_command_tests.sample_d())
#     layout = None
#     set_ui_model_command_layout(lcs, command_d, layout)
#     lcs.set.assert_called_once()


# def test_set_ui_model_commands():
#     lcs = Mock()
#     model = "Sample model"
#     commands = ["Sample 1", "Sample 2"]
#     set_ui_model_commands(lcs, model, commands)
#     lcs.set.assert_called_once()
