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


def _make_sample_command():
    d_res = data_to_res(htypes.model_commands_tests.sample_d())
    model_impl = htypes.ui.model_command_impl(
        function=fn_to_ref(_sample_command_fn),
        params=('piece', 'ctx'),
        )
    return htypes.ui.model_command(
        d=mosaic.put(d_res),
        impl=mosaic.put(model_impl),
        )


def test_list_model_commands():
    lcs = Mock()
    lcs.get.return_value = None  # Missint (empty) command list.

    sample_command = _make_sample_command()
    model_t = htypes.model_commands_tests.sample_model_1

    t_res = pyobj_creg.actor_to_piece(model_t)
    d_res = data_to_res(htypes.ui.model_command_d())
    association_reg[d_res, t_res] = sample_command

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
    sample_command = _make_sample_command()
    ctx = Context()
    model = htypes.model_commands_tests.sample_model_1()
    model_state = htypes.model_commands_tests.sample_model_state()
    piece = htypes.model_commands.model_commands(
        model=mosaic.put(model),
        model_state=mosaic.put(model_state)
        )
    current_item = htypes.model_commands.item(
        command=mosaic.put(sample_command),
        name="<unused>",
        impl="<unused>",
        )
    result = await model_commands.run_command(piece, current_item, ctx)
    assert result
    assert result == "Sample result"
