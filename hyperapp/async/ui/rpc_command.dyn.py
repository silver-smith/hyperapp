import logging

from hyperapp.common.htypes import (
    optional_mt,
    field_mt,
    record_mt,
    name_wrapped_mt,
    ref_t,
    )
from hyperapp.common.module import Module

from . import htypes
from .object_command import Command

log = logging.getLogger(__name__)


class RpcElementCommand:

    @classmethod
    async def from_piece(cls, piece, mosaic, peer_registry, async_rpc_call_factory, rpc_endpoint, identity):
        peer = peer_registry.invite(piece.peer_ref)
        rpc_call = async_rpc_call_factory(rpc_endpoint, peer, piece.servant_fn_ref, identity)

        return cls(mosaic, peer, piece.servant_fn_ref, rpc_call, piece.state_attr_list, piece.name)

    def __init__(self, mosaic, peer, servant_fn_ref, rpc_call, state_attr_list, name):
        self._mosaic = mosaic
        self._peer = peer
        self._servant_fn_ref = servant_fn_ref
        self._rpc_call = rpc_call
        self._state_attr_list = state_attr_list
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def kind(self):
        return 'object'

    @property
    def dir(self):
        return [htypes.rpc_command.rpc_command_d(
            peer_ref=self._mosaic.put(self._peer.piece),
            servant_fn_ref=self._servant_fn_ref,
            )]

    @property
    def piece(self):
        return htypes.rpc_command.rpc_command(
            peer_ref=self._mosaic.put(self._peer.piece),
            servant_fn_ref=self._servant_fn_ref,
            state_attr_list=self._state_attr_list,
            name=self._name,
            )

    async def run(self, object, view_state, origin_dir):
        args = [
            getattr(view_state, attr)
            for attr in self._state_attr_list
            ]
        piece = await self._rpc_call(*args)
        return piece


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

    # Required client_rpc_endpoint registered at services only by async_init.
    async def async_init(self, services):
        services.command_registry.register_actor(
            htypes.rpc_command.rpc_command,
            RpcElementCommand.from_piece,
            services.mosaic,
            services.peer_registry,
            services.async_rpc_call_factory,
            services.client_rpc_endpoint,
            services.client_identity,
            )
