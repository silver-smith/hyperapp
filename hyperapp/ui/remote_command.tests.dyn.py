from . import htypes
from .services import (
    mosaic,
    )
from .tested.code import remote_command


def test_enum(generate_rsa_identity):
    my_identity = generate_rsa_identity(fast=True)
    remote_identity = generate_rsa_identity(fast=True)
    model = htypes.remote_command_tests.sample_model()
    remote_model = htypes.model.remote_model(
        model=mosaic.put(model),
        remote_peer=mosaic.put(remote_identity.peer.piece),
        )
    command_list = remote_command.remote_command_enum(remote_model, my_identity)
