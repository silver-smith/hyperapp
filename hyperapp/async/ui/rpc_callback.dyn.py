import logging

from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


class RpcCallback:

    @classmethod
    async def from_piece(cls, piece, mosaic, peer_registry, servant_path_from_data, async_rpc_call, rpc_endpoint, identity):
        peer = peer_registry.invite(piece.peer_ref)
        servant_path = servant_path_from_data(piece.servant_path)
        rpc_call = async_rpc_call(rpc_endpoint, peer, servant_path, identity)

        return cls(mosaic, peer, servant_path, rpc_call, piece.item_attr)

    def __init__(self, mosaic, peer, servant_path, rpc_call, item_attr):
        self._mosaic = mosaic
        self._peer = peer
        self._servant_path = servant_path
        self._rpc_call = rpc_call
        self._item_attr = item_attr

    @property
    def piece(self):
        return htypes.rpc_callback.rpc_callback(
            peer_ref=self._mosaic.put(self._peer.piece),
            servant_path=self._servant_path.as_data(self._mosaic),
            item_attr=self._item_attr,
            )

    async def run(self, item):
        value = getattr(item, self._item_attr)
        return await self._rpc_call(value)


class ThisModule(Module):

    # Required client_rpc_endpoint registered at services only by async_init.
    async def async_init(self, services):
        services.callback_registry.register_actor(
            htypes.rpc_callback.rpc_callback,
            RpcCallback.from_piece,
            services.mosaic,
            services.peer_registry,
            services.servant_path_from_data,
            services.async_rpc_call,
            services.client_rpc_endpoint,
            services.client_identity,
            )
