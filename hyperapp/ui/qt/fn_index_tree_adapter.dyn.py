from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.tree_adapter import FnIndexTreeAdapterBase


class FnIndexTreeAdapter(FnIndexTreeAdapterBase):

    @classmethod
    @mark.actor.ui_adapter_creg(htypes.tree_adapter.fn_index_tree_adapter)
    def from_piece(cls, piece, model, ctx, system_fn_creg, feed_factory, rpc_call_factory):
        item_t = pyobj_creg.invite(piece.item_t)
        fn = system_fn_creg.invite(piece.system_fn)
        return cls(feed_factory, rpc_call_factory, model, item_t, ctx, fn)

    def __init__(self, feed_factory, rpc_call_factory, model, item_t, ctx, fn):
        super().__init__(feed_factory, model, item_t)
        self._rpc_call_factory = rpc_call_factory
        self._ctx = ctx
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
                servant_ref=self._fn.partial_ref(self._ctx, **kw),
                )
            return rpc_call()
        return self._fn.call(self._ctx, **kw)


@mark.actor.ui_type_creg
def tree_ui_type_layout(piece, system_fn_ref):
    adapter = htypes.tree_adapter.fn_index_tree_adapter(
        item_t=piece.item_t,
        # key_t=ui_t.key_t,
        system_fn=system_fn_ref,
        )
    return htypes.tree.view(mosaic.put(adapter))
