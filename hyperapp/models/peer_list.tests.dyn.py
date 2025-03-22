from unittest.mock import MagicMock, Mock, patch

from hyperapp.boot.htypes.packet_coders import packet_coders

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .code.model_command import UnboundModelCommand
from .fixtures import feed_fixtures
from .tested.code import peer_list


@mark.fixture
def piece():
    return htypes.peer_list.model()


@mark.fixture.obj
def peer_name():
    return "Sample peer"


@mark.fixture
def file_bundle_factory(generate_rsa_identity, peer_name, path):
    identity = generate_rsa_identity(fast=True)
    mock = Mock()
    if 'peer_list' in str(path):
        mock.load_piece.return_value = htypes.peer_list.bundle(
            peer_list=(
                htypes.peer_list.peer(
                    name=peer_name,
                    peer=mosaic.put(identity.peer.piece),
                    ),
                ),
            )
    elif 'server/peer' in str(path):
        mock.load_piece.return_value = identity.peer.piece
    else:
        assert False, f"Unexpected path: {path!r}"
    return mock


@mark.fixture.obj
def peer_label_reg():
    return MagicMock()


def test_model(piece):
    item_list = peer_list.peer_list_model(piece)
    assert type(item_list) is list


def test_add_localhost(peer_label_reg, piece):
    host = 'localhost'
    peer_list.add(piece, host)
    peer_label_reg.__setitem__.assert_called_once()


def test_add_remote(bundler, generate_rsa_identity, peer_label_reg, piece):
    host = 'example-host'
    identity = generate_rsa_identity(fast=True)
    bundle = bundler([mosaic.put(identity.peer.piece)]).bundle
    data_json = packet_coders.encode('json', bundle, htypes.builtin.bundle)
    with patch.object(peer_list, 'subprocess') as subprocess:
        subprocess.check_output.return_value = data_json
        peer_list.add(piece, host)
    peer_label_reg.__setitem__.assert_called_once()



async def test_remove(feed_factory, piece, peer_name):
    feed = feed_factory(piece)
    current_idx = 0
    current_item = htypes.peer_list.item(
        name=peer_name,
        peer=mosaic.put("<unused>"),
        peer_repr="<unused>",
        )
    await peer_list.remove(piece, current_idx, current_item)
    await feed.wait_for_diffs(count=1)


@mark.fixture
def current_item(generate_rsa_identity):
    identity = generate_rsa_identity(fast=True)
    return htypes.peer_list.item(
        name="Sample peer",
        peer=mosaic.put(identity.peer.piece),
        peer_repr="<unused>",
        )


def test_open_model(piece, current_item):
    model = htypes.model_list.model_arg(
        model_t=pyobj_creg.actor_to_ref(htypes.peer_list_tests.sample_model),
        )
    remote_model = peer_list.open_model(piece, current_item, model)
    assert isinstance(remote_model, htypes.model.remote_model)


def _sample_fn():
    return 'sample-fn'


@mark.fixture
def command_d():
    return htypes.peer_list_tests.sample_command_d()


@mark.config_fixture('global_model_command_reg')
def global_model_command_reg_config(partial_ref, command_d):
    fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=(),
        service_params=(),
        raw_fn=_sample_fn,
        bound_fn=_sample_fn,
        )
    command = UnboundModelCommand(
        d=command_d,
        ctx_fn=fn,
        properties=htypes.command.properties(False, False, False),
        )
    return [command]


@mark.fixture
def rpc_call_factory(receiver_peer, sender_identity, servant_ref):
    def call():
        return "Sample result"
    return call


async def test_run_global_command(generate_rsa_identity, piece, current_item, command_d):
    identity = generate_rsa_identity(fast=True)
    ctx = Context(
        identity=identity,
        )
    command = htypes.global_commands.command_arg(
        d=mosaic.put(command_d),
        )
    result = await peer_list.run_command(piece, current_item, command, identity, ctx)
    assert result == "Sample result"


def test_open():
    piece = peer_list.open_peer_list()
    assert piece


def test_format_model(piece):
    title = peer_list.format_model(piece)
    assert type(title) is str
