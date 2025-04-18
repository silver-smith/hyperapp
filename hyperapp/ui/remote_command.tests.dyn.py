from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .code.model_command import ModelCommandFn, UnboundModelCommand
from .tested.code import remote_command



@mark.fixture
def rpc_system_call_factory(receiver_peer, sender_identity, fn):
    def call(**kw):
        return "remote-sample-result"
    return call


def sample_command():
    return 'local-sample-result'


@mark.fixture
def sample_command_fn(rpc_system_call_factory):
    return ModelCommandFn(
        rpc_system_call_factory=rpc_system_call_factory,
        ctx_params=(),
        service_params=(),
        raw_fn=sample_command,
        bound_fn=sample_command,
        )


@mark.fixture
def remote_model(generate_rsa_identity):
    remote_identity = generate_rsa_identity(fast=True)
    model = htypes.remote_command_tests.sample_model()
    return htypes.model.remote_model(
        model=mosaic.put(model),
        remote_peer=mosaic.put(remote_identity.peer.piece),
        )


async def test_remote_command_from_model_command(
        generate_rsa_identity, remote_command_from_model_command, sample_command_fn, remote_model):
    my_identity = generate_rsa_identity(fast=True)
    remote_identity = generate_rsa_identity(fast=True)
    command_d = htypes.remote_command_tests.sample_command_d()
    model_command = UnboundModelCommand(
        d=command_d,
        ctx_fn=sample_command_fn,
        properties=htypes.command.properties(False, False, False),
        )
    command = remote_command_from_model_command(remote_identity.peer, model_command)
    assert isinstance(command, remote_command.UnboundRemoteCommand)
    # Test run method, pick model.remote_model type.
    ctx = Context(
        identity=my_identity,
        model=remote_model,
        )
    bound_command = command.bind(ctx)
    result = await bound_command.run()
    assert result == "remote-sample-result", result


def test_enum(generate_rsa_identity, remote_model):
    my_identity = generate_rsa_identity(fast=True)
    ctx = Context(
        identity=my_identity,
        model=remote_model,
        )
    command_list = remote_command.remote_command_enum(remote_model, ctx)
