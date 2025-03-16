import logging
from pathlib import Path

from . import htypes
from .code.mark import mark

log = logging.getLogger(__name__)


peer_list_path = Path.home() / '.local/share/hyperapp/client/peer_list.yaml'


class PeerList:

    def __init__(self, file_bundle, peer_registry, path):
        self._file_bundle = file_bundle
        self._peer_registry = peer_registry
        self._path = path

    def values(self):
        try:
            bundle = self._file_bundle.load_piece()
        except FileNotFoundError:
            return []
        return [
            self._peer_registry.invite(peer_ref)
            for peer_ref in bundle.peer_list
            ]


@mark.service
def peer_list_reg(file_bundle_factory, peer_registry):
    bundle = file_bundle_factory(peer_list_path)
    return PeerList(bundle, peer_registry, peer_list_path)

    
@mark.model
def peer_list_model(piece, peer_list_reg):
    return [
        htypes.peer_list.item(
            repr=repr(peer),
            )
        for peer in peer_list_reg.values()
        ]


@mark.command(args=['host'])
def peer_list_add(piece, host):
    log.info("Peer list: Add host: %r", host)
    if host in {'', 'localhost'}:
        pass


@mark.global_command
def open_peer_list():
    return htypes.peer_list.model()


@mark.actor.formatter_creg
def format_model(piece):
    return "Peer list"
