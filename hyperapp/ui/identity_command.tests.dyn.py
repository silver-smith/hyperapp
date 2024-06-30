from unittest.mock import Mock

from . import htypes
from .services import (
    data_to_res,
    fn_to_ref,
    mosaic,
    )
from .code.context import Context
from .tested.code import identity_command


def _sample_command_fn(piece, ctx):
    return "Sample result"


def _make_sample_command():
    d_res = data_to_res(htypes.identity_command_tests.sample_d())
    model_impl = htypes.ui.model_command_impl(
        function=fn_to_ref(_sample_command_fn),
        params=('piece', 'ctx'),
        )
    return htypes.ui.model_command(
        d=mosaic.put(d_res),
        impl=mosaic.put(model_impl),
        )


def test_add_identity_command():
    sample_command = _make_sample_command()
    lcs = Mock()
    lcs.get.return_value = None  # Imitate missing command list; do not return Mock instance.
    ctx = Context()
    model = htypes.identity_command_tests.sample_model()
    model_state = htypes.identity_command_tests.sample_model_state()
    piece = htypes.model_commands.model_commands(
        model=mosaic.put(model),
        model_state=mosaic.put(model_state)
        )
    identity_command.add_identity_command(piece, lcs)
    lcs.set.assert_called_once()


def test_identity_command_instance():
    model = htypes.identity_command_tests.sample_model()
    ctx = Context(piece=model)
    piece = htypes.identity_command.identity_model_command_impl()
    impl = identity_command.identity_model_command_impl_from_piece(piece, ctx)
    assert impl.properties
