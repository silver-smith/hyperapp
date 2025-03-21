from . import htypes
from .services import (
    mosaic,
    )
from .tested.code import remote_model as remote_model_module


def test_format_remote_model(generate_rsa_identity):
    identity = generate_rsa_identity(fast=True)
    model = htypes.remote_model_tests.sample_model()
    remote_model = htypes.model.remote_model(
        model=mosaic.put(model),
        remote_peer=mosaic.put(identity.peer.piece),
        )
    title = remote_model_module.format_remote_model(remote_model)
    assert type(title) is str
