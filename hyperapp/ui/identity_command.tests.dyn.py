from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .code.context import Context
from .fixtures import feed_fixtures
from .tested.code import identity_command


def _sample_command_fn(piece, ctx):
    return "Sample result"


def _make_sample_command():
    d = htypes.identity_command_tests.sample_d()
    model_impl = htypes.ui.model_command_impl(
        function=fn_to_ref(_sample_command_fn),
        params=('piece', 'ctx'),
        )
    return htypes.ui.model_command(
        d=mosaic.put(d),
        impl=mosaic.put(model_impl),
        )


async def test_command_instance():
    d = htypes.identity_command_tests.sample_command_d()
    piece = htypes.identity_command.identity_command(
        d=mosaic.put(d),
        )
    unbound_command = identity_command.UnboundIdentityModelCommand.from_piece(piece)
    assert unbound_command.properties

    model = htypes.identity_command_tests.sample_model()
    ctx = Context(
        model=model,
        piece=model,
        )
    bound_command = unbound_command.bind(ctx)
    assert bound_command.enabled
    result = await bound_command.run()
    assert result == model


async def test_add_command(feed_factory):
    lcs = Mock()
    lcs.get.return_value = None  # Imitate missing command list; do not return Mock instance.
    model = htypes.identity_command_tests.sample_model()
    model_state = htypes.identity_command_tests.sample_model_state()
    piece = htypes.model_commands.model(
        model=mosaic.put(model),
        model_state=mosaic.put(model_state)
        )
    feed = feed_factory(piece)
    ctx = Context()
    await identity_command.add_identity_command(piece, lcs, ctx)
    lcs.set.assert_called_once()
    await feed.wait_for_diffs(count=1)
