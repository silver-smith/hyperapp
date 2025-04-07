from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.tree_adapter import IndexTreeAdapterMixin, KeyTreeAdapterMixin, FnTreeAdapterBase


class FnTreeAdapter(FnTreeAdapterBase):

    @staticmethod
    def _resolve_model(peer_registry, model):
        if isinstance(model, htypes.model.remote_model):
            remote_peer = peer_registry.invite(model.remote_peer)
            model = web.summon(model.model)
        else:
            remote_peer = None
        return (remote_peer, model)

    def __init__(self, rpc_call_factory, feed_factory, model, item_t, remote_peer, ctx, fn):
        super().__init__(feed_factory, model, item_t)
        self._rpc_call_factory = rpc_call_factory
        self._remote_peer = remote_peer
        self._ctx = ctx
        self._fn = fn

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
        return self._fn.call(self._ctx, **kw)


class FnIndexTreeAdapter(FnTreeAdapter, IndexTreeAdapterMixin):

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx, system_fn_creg, rpc_call_factory, peer_registry, feed_factory):
        item_t = pyobj_creg.invite(piece.item_t)
        fn = system_fn_creg.invite(piece.system_fn)
        remote_peer, model = cls._resolve_model(peer_registry, model)
        return cls(rpc_call_factory, feed_factory, model, item_t, remote_peer, ctx, fn)


class FnKeyTreeAdapter(FnTreeAdapter, KeyTreeAdapterMixin):

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx, system_fn_creg, rpc_call_factory, peer_registry, feed_factory):
        item_t = pyobj_creg.invite(piece.item_t)
        fn = system_fn_creg.invite(piece.system_fn)
        remote_peer, model = cls._resolve_model(peer_registry, model)
        key_field_t = pyobj_creg.invite(piece.key_field_t)
        return cls(rpc_call_factory, feed_factory, model, item_t, remote_peer, ctx, fn, piece.key_field, key_field_t)

    def __init__(self, rpc_call_factory, feed_factory, model, item_t, remote_peer, ctx, fn, key_field, key_field_t):
        super().__init__(rpc_call_factory, feed_factory, model, item_t, remote_peer, ctx, fn)
        KeyTreeAdapterMixin.__init__(self, key_field, key_field_t)


@mark.actor.ui_type_creg
def index_tree_ui_type_layout(piece, system_fn_ref):
    adapter = htypes.tree_adapter.fn_index_tree_adapter(
        item_t=piece.item_t,
        system_fn=system_fn_ref,
        )
    return htypes.tree.view(mosaic.put(adapter))


@mark.actor.ui_type_creg
def key_tree_ui_type_layout(piece, system_fn_ref):
    adapter = htypes.tree_adapter.fn_key_tree_adapter(
        item_t=piece.item_t,
        system_fn=system_fn_ref,
        key_field=piece.key_field,
        key_field_t=piece.key_field_t,
        )
    return htypes.tree.view(mosaic.put(adapter))
