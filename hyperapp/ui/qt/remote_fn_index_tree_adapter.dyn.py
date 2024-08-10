from . import htypes
from .services import (
    mark,
    pyobj_creg,
    )
from .code.tree_adapter import FnIndexTreeAdapterBase


class RemoteFnIndexTreeAdapter(FnIndexTreeAdapterBase):

    @classmethod
    def from_piece(cls, piece, model, ctx, feed_factory):
        element_t = pyobj_creg.invite(piece.element_t)
        remote_peer = peer_registry.invite(piece.remote_peer)
        return cls(feed_factory, model, element_t, piece.params, ctx, piece.function, ctx.identity, remote_peer)

    def __init__(self, feed_factory, model, item_t, params, ctx, fn_res_ref, identity, remote_peer):
        super().__init__(feed_factory, model, item_t, params, ctx)
        self._rpc_call = rpc_call_factory(
            receiver_peer=remote_peer,
            servant_ref=fn_res_ref,
            sender_identity=identity,
            )

    def _call_fn(self, **kw):
        return self._rpc_call(**kw)
