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
    web,
    )
from .code.mark import mark
from .code.list_diff import IndexListDiff
from .code.ui_model_command import split_command_result

log = logging.getLogger(__name__)


peer_list_path = Path.home() / '.local/share/hyperapp/client/peer_list.json'
server_bundle_path = '.local/share/hyperapp/server/peer.json'


Peer = namedtuple('Peer', 'name peer')


class PeerList:

    def __init__(self, file_bundle, peer_creg, path):
        self._file_bundle = file_bundle
        self._peer_creg = peer_creg
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
            Peer(rec.name, self._peer_creg.invite(rec.peer))
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
def peer_list_reg(file_bundle_factory, peer_creg):
    bundle = file_bundle_factory(peer_list_path)
    return PeerList(bundle, peer_creg, peer_list_path)

    
@mark.model(key='name')
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
    unbundler.register_bundle(bundle, register_associations=True)
    return bundle.roots[0]


@mark.command.add(args=['host'])
def add(piece, host, peer_list_reg, file_bundle_factory, peer_creg, peer_label_reg):
    log.info("Peer list: Add host: %r", host)
    if host in {'', 'localhost'}:
        path = Path.home() / server_bundle_path
        bundle = file_bundle_factory(path)
        peer = peer_creg.animate(bundle.load_piece())
        log.info("Loaded local server peer from: %s", bundle.path)
        label = 'localhost'
    else:
        command = ['ssh', host, 'cat', server_bundle_path]
        bundle_json = subprocess.check_output(command)
        peer_ref = _unpack_bundle(bundle_json)
        peer = peer_creg.invite(peer_ref)
        log.info("Loaded server %r peer", host)
        label = host
    peer_list_reg.add(label, peer)
    peer_label_reg[peer.piece] = label
    return label


@mark.command.remove
async def remove(piece, current_item, peer_list_reg):
    log.info("Peer list: Remove host: %r", current_item.name)
    return peer_list_reg.remove(current_item.name)


@mark.command(args=['command'])
async def open_model(piece, current_item, command, ctx, peer_creg, global_model_command_reg):
    command_d = web.summon(command.d)
    command = global_model_command_reg[command_d]
    peer = peer_creg.invite(current_item.peer)
    log.info("Peer list: Open model from global command %s @ %s (%s)", command, current_item.name, repr(peer))
    bound_command = command.bind(ctx)
    result = await bound_command.run()
    log.info("Run global command result: %s", result)
    model, key = split_command_result(result)
    remote_model = htypes.model.remote_model(
        model=mosaic.put(model),
        remote_peer=mosaic.put(peer.piece),
        )
    return (remote_model, key)


@mark.command(args=['command'])
async def run_command(piece, current_item, command, ctx,
                      peer_creg, global_model_command_reg, remote_command_from_model_command):
    command_d = web.summon(command.d)
    peer = peer_creg.invite(current_item.peer)
    log.info("Peer list: Run global command %s @ %s (%s)", command_d, current_item.name, repr(peer))
    command = global_model_command_reg[command_d]
    remote_command = remote_command_from_model_command(peer, command)
    bound_command = remote_command.bind(ctx)
    result = await bound_command.run()
    log.info("Run remote global command result: %s", result)
    return result


@mark.global_command
def open_peer_list():
    return htypes.peer_list.model()


@mark.actor.formatter_creg
def format_model(piece):
    return "Peer list"
