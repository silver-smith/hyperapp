import logging
import subprocess
from collections import namedtuple
from functools import cached_property
from pathlib import Path

from hyperapp.boot.htypes.packet_coders import packet_coders

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    unbundler,
    )
from .code.mark import mark
from .code.list_diff import ListDiff

log = logging.getLogger(__name__)


peer_list_path = Path.home() / '.local/share/hyperapp/client/peer_list.json'
server_bundle_path = '.local/share/hyperapp/server/peer.json'


Peer = namedtuple('Peer', 'name peer')


class PeerList:

    def __init__(self, file_bundle, peer_registry, path):
        self._file_bundle = file_bundle
        self._peer_registry = peer_registry
        self._path = path

    def values(self):
        return self._peer_list

    def add(self, name, peer):
        peer_list = self._peer_list
        peer_list.append(Peer(name, peer))
        self._save(peer_list)

    def remove(self, name):
        peer_list = self._peer_list
        for idx, rec in enumerate(self._peer_list):
            if rec.name == name:
                del peer_list[idx]
                break
        else:
            log.warning("Peer list: Can not remove host %r; it is not in the list", name)
            return False
        self._save(peer_list)
        return True

    @cached_property
    def _peer_list(self):
        try:
            bundle = self._file_bundle.load_piece()
        except FileNotFoundError:
            return []
        return [
            Peer(rec.name, self._peer_registry.invite(rec.peer))
            for rec in bundle.peer_list
            ]

    def _save(self, peer_list):
        bundle = htypes.peer_list.bundle(
            peer_list=tuple(
                htypes.peer_list.peer(
                    name=rec.name,
                    peer=mosaic.put(rec.peer.piece),
                    )
                for rec in peer_list
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
            name=rec.name,
            peer=mosaic.put(rec.peer.piece),
            peer_repr=repr(rec.peer),
            )
        for rec in peer_list_reg.values()
        ]


def _unpack_bundle(json_data):
    bundle = packet_coders.decode('json', json_data, htypes.builtin.bundle)
    unbundler.register_bundle(bundle, register_associations=False)
    return bundle.roots[0]


@mark.command(args=['host'])
def add(piece, host, peer_list_reg, file_bundle_factory, peer_registry):
    log.info("Peer list: Add host: %r", host)
    if host in {'', 'localhost'}:
        path = Path.home() / server_bundle_path
        bundle = file_bundle_factory(path)
        peer = peer_registry.animate(bundle.load_piece())
        log.info("Loaded local server peer from: %s", bundle.path)
        peer_list_reg.add('localhost', peer)
        return
    command = ['ssh', host, 'cat', server_bundle_path]
    bundle_json = subprocess.check_output(command)
    peer_ref = _unpack_bundle(bundle_json)
    peer = peer_registry.invite(peer_ref)
    log.info("Loaded server %r peer", host)
    peer_list_reg.add(host, peer)


@mark.command
async def remove(piece, current_idx, current_item, feed_factory, peer_list_reg):
    log.info("Peer list: Remove host #%d: %r", current_idx, current_item.name)
    feed = feed_factory(piece)
    if peer_list_reg.remove(current_item.name):
        await feed.send(ListDiff.Remove(current_idx))


@mark.command(args=['model'])
def open_model(piece, current_item, model, peer_registry):
    model_t = pyobj_creg.invite(model.model_t)
    peer = peer_registry.invite(current_item.peer)
    log.info("Peer list: Open model %s @ %s (%s)", model_t, current_item.name, repr(peer))
    if model_t.fields:
        log.info("Model %s has fields, do not know how to make an instance", model_t)
        return
    model = model_t()
    return htypes.model.remote_model(
        model=mosaic.put(model),
        remote_peer=mosaic.put(peer.piece),
        )


@mark.global_command
def open_peer_list():
    return htypes.peer_list.model()


@mark.actor.formatter_creg
def format_model(piece):
    return "Peer list"
