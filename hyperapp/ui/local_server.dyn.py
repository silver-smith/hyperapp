import logging
from pathlib import Path

from hyperapp.boot import dict_coders

from .code.mark import mark

log = logging.getLogger(__name__)


@mark.service
def local_server_peer_path():
    return Path.home() / '.local/share/hyperapp/server/peer.json'


@mark.service
def local_server_peer(peer_registry, file_bundle, local_server_peer_path):
    peer_bundle = file_bundle(local_server_peer_path)
    try:
        server_peer = peer_registry.animate(peer_bundle.load_piece())
        log.info("Server peer: loaded from: %s", peer_bundle.path)
        return server_peer
    except FileNotFoundError:
        return None
