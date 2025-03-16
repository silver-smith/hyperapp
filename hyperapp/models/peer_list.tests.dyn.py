from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .tested.code import peer_list
from .code.mark import mark


@mark.fixture
def model():
    return htypes.peer_list.model()


@mark.fixture
def file_bundle(generate_rsa_identity, path):
    identity = generate_rsa_identity(fast=True)
    mock = Mock()
    bundle = htypes.peer_list.bundle(
        peer_list=[mosaic.put(identity.peer.piece)],
        )
    mock.load_piece.return_value = bundle
    return mock


def test_model(model):
    item_list = peer_list.peer_list_model(model)
    assert type(item_list) is list


def test_open():
    model = peer_list.open_peer_list()
    assert model


def test_format_model(model):
    title = peer_list.format_model(model)
    assert type(title) is str
