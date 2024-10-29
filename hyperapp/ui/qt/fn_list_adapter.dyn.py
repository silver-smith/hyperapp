import logging

from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.mark import mark
from .code.list_adapter import FnListAdapterBase

log = logging.getLogger(__name__)


class FnListAdapter(FnListAdapterBase):

    @classmethod
    @mark.actor.ui_adapter_creg(htypes.list_adapter.fn_list_adapter)
    def from_piece(cls, piece, model, ctx, system_fn_creg, rpc_call_factory, feed_factory):
        element_t = pyobj_creg.invite(piece.element_t)
        fn = system_fn_creg.invite(piece.system_fn)
        return cls(rpc_call_factory, feed_factory, model, element_t, ctx, fn)

    def __init__(self, rpc_call_factory, feed_factory, model, item_t, ctx, fn):
        super().__init__(feed_factory, model, item_t)
        self._rpc_call_factory = rpc_call_factory
        self._ctx = ctx
        self._fn = fn

    @property
    def function(self):
        return self._fn

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
