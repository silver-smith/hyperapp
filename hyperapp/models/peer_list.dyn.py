import logging
from functools import cached_property
from pathlib import Path

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark

log = logging.getLogger(__name__)


peer_list_path = Path.home() / '.local/share/hyperapp/client/peer_list.yaml'
server_bundle_path = '.local/share/hyperapp/server/peer.json'


class PeerList:

    def __init__(self, file_bundle, peer_registry, path):
        self._file_bundle = file_bundle
        self._peer_registry = peer_registry
        self._path = path

    def values(self):
        return self._peer_list

    def add(self, peer):
        peer_list = self._peer_list
        peer_list.append(peer)
        self._save(peer_list)

    @cached_property
    def _peer_list(self):
        try:
            bundle = self._file_bundle.load_piece()
        except FileNotFoundError:
            return []
        return [
            self._peer_registry.invite(peer_ref)
            for peer_ref in bundle.peer_list
            ]

    def _save(self, peer_list):
        bundle = htypes.peer_list.bundle(
            peer_list=tuple(
                mosaic.put(peer.piece)
                for peer in peer_list
                ),
            )
        log.info("Peer list: Save %d peers to %s", len(peer_list), self._file_bundle.path)
        self._file_bundle.save_piece(bundle)


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
def peer_list_add(piece, host, peer_list_reg, file_bundle_factory, peer_registry):
    log.info("Peer list: Add host: %r", host)
    if host in {'', 'localhost'}:
        path = Path.home() / server_bundle_path
        peer_bundle = file_bundle_factory(path)
        peer = peer_registry.animate(peer_bundle.load_piece())
        log.info("Loaded local server peer from: %s", peer_bundle.path)
        peer_list_reg.add(peer)


@mark.global_command
def open_peer_list():
    return htypes.peer_list.model()


@mark.actor.formatter_creg
def format_model(piece):
    return "Peer list"
