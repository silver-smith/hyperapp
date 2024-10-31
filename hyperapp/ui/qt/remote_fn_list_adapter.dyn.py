import logging

from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.mark import mark
from .code.list_adapter import FnListAdapterBase

log = logging.getLogger(__name__)


class RemoteFnListAdapter(FnListAdapterBase):

    @classmethod
    @mark.actor.ui_adapter_creg(htypes.list_adapter.remote_fn_list_adapter)
    def from_piece(cls, piece, model, ctx, system_fn_creg, peer_registry, rpc_call_factory, feed_factory):
        item_t = pyobj_creg.invite(piece.item_t)
        remote_peer = peer_registry.invite(piece.remote_peer)
        fn = system_fn_creg.invite(piece.system_fn)
        return cls(rpc_call_factory, feed_factory, model, item_t, ctx, fn, ctx.identity, remote_peer)

    def __init__(self, rpc_call_factory, feed_factory, model, item_t, ctx, fn, identity, remote_peer):
        super().__init__(feed_factory, model, item_t)
        self._rpc_call_factory = rpc_call_factory
        self._ctx = ctx
        self._fn = fn
        self._remote_peer = remote_peer
        self._identity = identity

    def _call_fn(self, **kw):
        rpc_call = self._rpc_call_factory(
            receiver_peer=self._remote_peer,
            sender_identity=self._identity,
            servant_ref=self._fn.partial_ref(self._ctx, **kw),
            )
        return rpc_call()
