import logging
from pathlib import Path

from hyperapp.common import dict_coders

from .services import (
    file_bundle,
    peer_registry,
    )    

log = logging.getLogger(__name__)


def local_server_peer():
    peer_bundle = file_bundle(Path.home() / '.local/share/hyperapp/server/peer.json')
    try:
        server_peer = peer_registry.animate(peer_bundle.load_piece())
        log.info("Server peer: loaded from: %s", peer_bundle.path)
        return server_peer
    except FileNotFoundError:
        return None
