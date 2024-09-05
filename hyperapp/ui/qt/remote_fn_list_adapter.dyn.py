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
    def from_piece(cls, piece, model, ctx, peer_registry, rpc_call_factory, feed_factory):
        element_t = pyobj_creg.invite(piece.element_t)
        remote_peer = peer_registry.invite(piece.remote_peer)
        return cls(rpc_call_factory, feed_factory, model, element_t, piece.params, ctx, piece.function, ctx.identity, remote_peer)

    def __init__(self, rpc_call_factory, feed_factory, model, item_t, params, ctx, fn_res_ref, identity, remote_peer):
        super().__init__(feed_factory, model, item_t, params, ctx)
        self._rpc_call = rpc_call_factory(
            receiver_peer=remote_peer,
            sender_identity=identity,
            servant_ref=fn_res_ref,
            )

    def _call_fn(self, **kw):
        return self._rpc_call(**kw)
