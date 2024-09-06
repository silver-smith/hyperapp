from unittest.mock import Mock

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    fn_to_ref,
    mosaic,
    pyobj_creg,
    )
from .code.context import Context
from .tested.code import model_commands


def test_browse_current_model():
    model_state = htypes.model_commands_tests.sample_model_state()
    model_1 = htypes.model_commands_tests.sample_model_1()
    piece_1 = model_commands.open_model_commands(model_1, model_state)
    assert piece_1
    model_2 = htypes.model_commands_tests.sample_model_2()
    piece_2 = model_commands.open_model_commands(model_2, model_state)
    assert piece_2


def _sample_command_fn(piece, ctx):
    return "Sample result"


def _make_sample_model_command():
    d_res = data_to_res(htypes.model_commands_tests.sample_d())
    impl = htypes.ui.model_command_impl(
        function=fn_to_ref(_sample_command_fn),
        params=('piece', 'ctx'),
        )
    command = htypes.ui.model_command(
        d=mosaic.put(d_res),
        impl=mosaic.put(impl),
        )
    return (impl, command)


def test_list_model_commands():
    lcs = Mock()
    lcs.get.return_value = None  # Missint (empty) command list.

    command_impl, sample_command = _make_sample_model_command()
    model_t = htypes.model_commands_tests.sample_model_1

    t_res = pyobj_creg.actor_to_piece(model_t)
    d_res = data_to_res(htypes.ui.model_command_d())
    association_reg[d_res, t_res] = sample_command

    props_d_res = data_to_res(htypes.ui.command_properties_d())
    association_reg[props_d_res, command_impl] = htypes.ui.command_properties(
        is_global=False,
        uses_state=False,
        remotable=False,
        )

    model = model_t()
    model_state = htypes.model_commands_tests.sample_model_state()
    piece = htypes.model_commands.model_commands(
        model=mosaic.put(model),
        model_state=mosaic.put(model_state)
        )
    ctx = Context()
    result = model_commands.list_model_commands(piece, ctx, lcs)
    assert result
    assert len(result) == 1
    assert result[0].name == 'sample'


async def test_run_command():
    _, sample_model_command = _make_sample_model_command()
    ui_impl = htypes.ui.ui_model_command_impl(
        model_command_impl=sample_model_command.impl,
        layout=None,
        )
    sample_ui_command = htypes.ui.ui_command(
        d=sample_model_command.d,
        impl=mosaic.put(ui_impl),
        )
    navigator = Mock()
    ctx = Context(
        lcs=Mock(),
        navigator=navigator,
        )
    model = htypes.model_commands_tests.sample_model_1()
    model_state = htypes.model_commands_tests.sample_model_state()
    piece = htypes.model_commands.model_commands(
        model=mosaic.put(model),
        model_state=mosaic.put(model_state)
        )
    current_item = htypes.model_commands.item(
        command=mosaic.put(sample_ui_command),
        name="<unused>",
        impl="<unused>",
        )
    await model_commands.run_command(piece, current_item, ctx)
    navigator.view.open.assert_called_once()
