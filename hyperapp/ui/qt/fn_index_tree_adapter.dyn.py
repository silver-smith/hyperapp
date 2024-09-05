from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.mark import mark
from .code.tree_adapter import FnIndexTreeAdapterBase


class FnIndexTreeAdapter(FnIndexTreeAdapterBase):

    @classmethod
    @mark.actor.ui_adapter_creg(htypes.tree_adapter.fn_index_tree_adapter)
    def from_piece(cls, piece, model, ctx, feed_factory, rpc_call_factory):
        element_t = pyobj_creg.invite(piece.element_t)
        fn = pyobj_creg.invite(piece.function)
        return cls(feed_factory, rpc_call_factory, model, element_t, piece.params, ctx, piece.function, fn)

    def __init__(self, feed_factory, rpc_call_factory, model, item_t, params, ctx, fn_res_ref, fn):
        super().__init__(feed_factory, model, item_t, params, ctx)
        self._rpc_call_factory = rpc_call_factory
        self._fn_res_ref = fn_res_ref
        self._fn = fn

    def _call_fn(self, **kw):
        try:
            identity = self._ctx.identity
            remote_peer = self._ctx.remote_peer
        except KeyError:
            pass
        else:
            rpc_call = self._rpc_call_factory(
                sender_identity=identity,
                receiver_peer=remote_peer,
                servant_ref=self._fn_res_ref,
                )
            return rpc_call(**kw)
        return self._fn(**kw)
