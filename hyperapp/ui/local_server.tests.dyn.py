from pathlib import Path

from .code.mark import mark
from .tested.code import local_server


@mark.fixture
def local_server_peer_path():
    return Path('/tmp/local-server-peer-test-non-existent.json')


def test_local_server_peer(local_server_peer):
    peer = local_server_peer
    assert not peer
