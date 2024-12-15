from unittest.mock import Mock

from . import htypes
from .code.system_fn import ContextFn
from .code.model_command import UnboundModelCommand
from .code.ui_model_command import UnboundUiModelCommand, CommandItem
from .tested.code import command_list_view


def _sample_fn(model, state):
    return f'sample-fn: {state}'


def test_command_item_to_item(data_to_ref, partial_ref, model_view_creg, visualizer):
    lcs = Mock()
    system_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('view', 'state'),
        service_params=(),
        raw_fn=_sample_fn,
        bound_fn=_sample_fn,
        )
    model_command = UnboundModelCommand(
        d=htypes.command_list_view_tests.sample_model_command_d(),
        ctx_fn=system_fn,
        properties=htypes.command.properties(False, False, False),
        )
    command = UnboundUiModelCommand(
        model_view_creg=model_view_creg,
        visualizer=visualizer,
        lcs=lcs,
        d=htypes.command_list_view_tests.sample_model_command_d(),
        model_command=model_command,
        layout=None,
        )
    command_item = CommandItem(
        d=htypes.command_list_view_tests.sample_command_d(),
        model_command_d=htypes.command_list_view_tests.sample_model_command_d(),
        command=command,
        )
    view_item = command_list_view.command_item_to_view_item(data_to_ref, command_item)
    assert view_item
