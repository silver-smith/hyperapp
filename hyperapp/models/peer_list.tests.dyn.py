from unittest.mock import Mock, patch

from hyperapp.boot.htypes.packet_coders import packet_coders

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
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


def test_add_localhost(piece):
    host = 'localhost'
    peer_list.add(piece, host)


def test_add_remote(bundler, generate_rsa_identity, piece):
    host = 'example-host'
    identity = generate_rsa_identity(fast=True)
    bundle = bundler([mosaic.put(identity.peer.piece)]).bundle
    data_json = packet_coders.encode('json', bundle, htypes.builtin.bundle)
    with patch.object(peer_list, 'subprocess') as subprocess:
        subprocess.check_output.return_value = data_json
        peer_list.add(piece, host)


def test_open_model(generate_rsa_identity, piece):
    identity = generate_rsa_identity(fast=True)
    current_item = htypes.peer_list.item(
        name="Sample peer",
        peer=mosaic.put(identity.peer.piece),
        peer_repr="<unused>",
        )
    model = htypes.model_list.model_arg(
        model_t=pyobj_creg.actor_to_ref(htypes.peer_list_tests.sample_model),
        )
    peer_list.open_model(piece, current_item, model)


def test_open():
    piece = peer_list.open_peer_list()
    assert piece


def test_format_model(piece):
    title = peer_list.format_model(piece)
    assert type(title) is str
