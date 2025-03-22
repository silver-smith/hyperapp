from . import htypes
from .services import (
    mosaic,
    )
from .code.system_fn import ContextFn
from .code.model_command import UnboundModelCommand
from .tested.code import remote_command



def _sample_fn():
    return 'sample-fn'


def test_remote_command_from_model_command(partial_ref, generate_rsa_identity, remote_command_from_model_command):
    my_identity = generate_rsa_identity(fast=True)
    remote_identity = generate_rsa_identity(fast=True)
    fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=(),
        service_params=(),
        raw_fn=_sample_fn,
        bound_fn=_sample_fn,
        )
    command_d = htypes.remote_command_tests.sample_command_d()
    model_command = UnboundModelCommand(
        d=command_d,
        ctx_fn=fn,
        properties=htypes.command.properties(False, False, False),
        )
    command = remote_command_from_model_command(my_identity, remote_identity.peer, model_command)
    assert isinstance(command, remote_command.UnboundRemoteCommand)


def test_enum(generate_rsa_identity):
    my_identity = generate_rsa_identity(fast=True)
    remote_identity = generate_rsa_identity(fast=True)
    model = htypes.remote_command_tests.sample_model()
    remote_model = htypes.model.remote_model(
        model=mosaic.put(model),
        remote_peer=mosaic.put(remote_identity.peer.piece),
        )
    command_list = remote_command.remote_command_enum(remote_model, my_identity)
