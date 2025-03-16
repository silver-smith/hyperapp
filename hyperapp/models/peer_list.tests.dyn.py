from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .tested.code import peer_list
from .code.mark import mark


@mark.fixture
def piece():
    return htypes.peer_list.model()


@mark.fixture
def file_bundle_factory(generate_rsa_identity, path):
    identity = generate_rsa_identity(fast=True)
    mock = Mock()
    if 'peer_list' in str(path):
        mock.load_piece.return_value = htypes.peer_list.bundle(
            peer_list=(
                htypes.peer_list.peer(
                    name="Sample peer",
                    peer=mosaic.put(identity.peer.piece),
                    ),
                ),
            )
    elif 'server/peer' in str(path):
        mock.load_piece.return_value = identity.peer.piece
    else:
        assert False, f"Unexpected path: {path!r}"
    return mock


def test_model(piece):
    item_list = peer_list.peer_list_model(piece)
    assert type(item_list) is list


def test_add(piece):
    host = 'localhost'
    peer_list.peer_list_add(piece, host)


def test_open():
    piece = peer_list.open_peer_list()
    assert piece


def test_format_model(piece):
    title = peer_list.format_model(piece)
    assert type(title) is str
