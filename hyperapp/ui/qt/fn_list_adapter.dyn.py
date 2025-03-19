import logging

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.list_adapter import FnListAdapterBase

log = logging.getLogger(__name__)


class FnListAdapter(FnListAdapterBase):

    @classmethod
    @mark.actor.ui_adapter_creg(htypes.list_adapter.fn_list_adapter)
    def from_piece(cls, piece, model, ctx, system_fn_creg, rpc_call_factory, feed_factory, column_visible_reg, peer_registry):
        item_t = pyobj_creg.invite(piece.item_t)
        fn = system_fn_creg.invite(piece.system_fn)
        if isinstance(model, htypes.model.remote_model):
            remote_peer = peer_registry.invite(model.remote_peer)
            model = web.summon(model.model)
        else:
            remote_peer = None
        return cls(rpc_call_factory, feed_factory, column_visible_reg, model, item_t, remote_peer, ctx, fn)

    def __init__(self, rpc_call_factory, feed_factory, column_visible_reg, model, item_t, remote_peer, ctx, fn):
        super().__init__(feed_factory, column_visible_reg, model, item_t)
        self._rpc_call_factory = rpc_call_factory
        self._remote_peer = remote_peer
        self._ctx = ctx
        self._fn = fn

    @property
    def function(self):
        return self._fn

    def _call_fn(self, **kw):
        if self._remote_peer:
            remote_peer = self._remote_peer
        else:
            try:
                remote_peer = self._ctx.remote_peer
            except KeyError:
                remote_peer = None
        if remote_peer:
            rpc_call = self._rpc_call_factory(
                sender_identity=self._ctx.identity,
                receiver_peer=remote_peer,
                servant_ref=self._fn.partial_ref(self._ctx, **kw),
                )
            return rpc_call()
        else:
            return self._fn.call(self._ctx, **kw)


@mark.actor.ui_type_creg
@mark.view_factory.ui_t
def list_ui_type_layout(piece, system_fn_ref):
    adapter = htypes.list_adapter.fn_list_adapter(
        item_t=piece.item_t,
        system_fn=system_fn_ref,
        )
    return htypes.list.view(mosaic.put(adapter))
