from . import htypes
from .services import (
    fn_to_res,
    mark,
    mosaic,
    )
from .code.context import Context
from .tested.code import model_commands


def test_browse_current_model():
    model_1 = htypes.model_commands_tests.sample_model_1()
    piece_1 = model_commands.open_model_commands(model_1)
    assert piece_1
    model_2 = htypes.model_commands_tests.sample_model_2()
    piece_2 = model_commands.open_model_commands(model_2)
    assert piece_2


def _phony_fn(piece, ctx):
    pass


def _make_sample_command():
    return htypes.ui.model_command(
        name="Sample model command",
        d=(),
        function=mosaic.put(fn_to_res(_phony_fn)),
        params=('piece', 'ctx'),
        )


@mark.service
def model_command_factory():
    def _model_command_factory(model):
        return [_make_sample_command()]
    return _model_command_factory


def test_list_model_commands():
    model = htypes.model_commands_tests.sample_model_1()
    piece = htypes.model_commands.model_commands(
        model=mosaic.put(model),
        )
    ctx = Context()
    result = model_commands.list_model_commands(piece, ctx)
    assert result
    assert len(result) == 1
    assert result[0].name == _make_sample_command().name
    assert result[0].params == "piece, ctx"


def test_run_command():
    model = htypes.model_commands_tests.sample_model_1()
    piece = htypes.model_commands.model_commands(
        model=mosaic.put(model),
        )
    current_item = htypes.model_commands.item(
        name=_make_sample_command().name,
        d="<unused>",
        params="<unused>",
        )
    result = model_commands.run_command(piece, current_item)
