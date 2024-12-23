from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.system_fn import ContextFn
from .code.model_command import UnboundModelCommand
from .code.ui_model_command import UnboundUiModelCommand, CommandItem
from .fixtures import feed_fixtures
from .tested.code import command_list_view


def _sample_fn(model, state):
    return f'sample-fn: {state}'


@mark.fixture
def lcs():
    lcs = Mock()
    lcs.get.return_value = None
    return lcs


def test_command_item_to_item(partial_ref, model_view_creg, visualizer, lcs):
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
    view_item = command_list_view.command_item_to_view_item(lcs, command_item)
    assert view_item


@mark.fixture
def current_item(data_to_ref):
    command_d = htypes.command_list_view_tests.sample_model_command_d()
    model_command_d = htypes.command_list_view_tests.sample_model_command_d()
    return htypes.command_list_view.item(
        ui_command_d=data_to_ref(command_d),
        model_command_d=data_to_ref(model_command_d),
        name="sample-command",
        groups="<unused>",
        repr="<unused>",
        shortcut="",
        text="",
        tooltip="",
        )


def mock_run_input_key_dialog():
    return ''


async def test_global_set_shortcut(feed_factory, lcs, current_item):
    piece = htypes.global_commands.view()
    feed = feed_factory(piece)
    command_list_view.run_key_input_dialog = mock_run_input_key_dialog
    await command_list_view.set_shortcut(piece, 0, current_item, lcs)
    lcs.set.assert_called_once()
    await feed.wait_for_diffs(count=1)


async def test_model_set_shortcut(feed_factory, lcs, current_item):
    model = htypes.command_list_view_tests.sample_model()
    model_state = htypes.command_list_view_tests.sample_model_state()
    piece = htypes.model_commands.view(
        model=mosaic.put(model),
        model_state=mosaic.put(model_state)
        )
    feed = feed_factory(piece)
    command_list_view.run_key_input_dialog = mock_run_input_key_dialog
    await command_list_view.set_shortcut(piece, 0, current_item, lcs)
    lcs.set.assert_called_once()
    await feed.wait_for_diffs(count=1)
