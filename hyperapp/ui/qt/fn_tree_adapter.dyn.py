import logging

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.tree_adapter import IndexTreeAdapterMixin, KeyTreeAdapterMixin, TreeAdapter

log = logging.getLogger(__name__)


class FnTreeAdapter(TreeAdapter):

    @staticmethod
    def _resolve_model(peer_registry, model):
        if isinstance(model, htypes.model.remote_model):
            remote_peer = peer_registry.invite(model.remote_peer)
            model = web.summon(model.model)
        else:
            remote_peer = None
        return (remote_peer, model)

    def __init__(self, partial_ref, rpc_call_factory, feed_factory, model, item_t, remote_peer, ctx, fn):
        super().__init__(model, item_t)
        self._partial_ref = partial_ref
        self._rpc_call_factory = rpc_call_factory
        self._remote_peer = remote_peer
        self._column_names = sorted(self._item_t.fields)
        self._ctx = ctx
        self._fn = fn
        self._lateral_ids = set()
        try:
            self._feed = feed_factory(model)
        except KeyError:
            self._feed = None
        else:
            self._feed.subscribe(self)

    def column_count(self):
        return len(self._column_names)

    def column_title(self, column):
        return self._column_names[column]

    def cell_data(self, id, column):
        item = self._id_to_item[id]
        return getattr(item, self._column_names[column])

    def _populate(self, parent_id):
        kw = {
            'model': self._model,
            'piece': self._model,
            **self._parent_model_kw(parent_id),
            }
        if self._remote_peer:
            remote_peer = self._remote_peer
        else:
            try:
                remote_peer = self._ctx.remote_peer
            except KeyError:
                remote_peer = None
        if remote_peer:
            self._remote_populate(parent_id, kw, remote_peer)
        else:
            self._local_populate(parent_id, kw)

    def _local_populate(self, parent_id, kw):
        item_list = self._fn.call(self._ctx, **kw)
        log.info("Fn tree adapter: retrieved local items for %s/%s: %s", self._model, parent_id, item_list)
        self._store_item_list(parent_id, item_list)

    def _remote_populate(self, parent_id, kw, remote_peer):
        fn_partial = self._fn.partial_ref(self._ctx, **kw)
        if parent_id != 0 and (pp_id := self._id_to_parent_id[parent_id]) in self._lateral_ids:
            is_lateral = True
            lateral_parent_id = pp_id
        else:
            is_lateral = False
            lateral_parent_id = parent_id
        wrapper_partial = self._servant_wrapper(fn_partial, is_lateral)
        rpc_call = self._rpc_call_factory(
            sender_identity=self._ctx.identity,
            receiver_peer=remote_peer,
            servant_ref=wrapper_partial,
            )
        item_list, children_rec_list = rpc_call()
        log.info("Fn tree adapter: retrieved remote items for %s/%s: %s", self._model, parent_id, item_list)
        self._store_item_list(parent_id, item_list)
        for rec in children_rec_list:
            item_id = self._children_rec_to_item_id(lateral_parent_id, rec)
            self._store_item_list(item_id, rec.item_list)
            self._lateral_ids.add(item_id)


class FnIndexTreeAdapter(FnTreeAdapter, IndexTreeAdapterMixin):

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx, partial_ref, system_fn_creg, rpc_call_factory, peer_registry, feed_factory):
        item_t = pyobj_creg.invite(piece.item_t)
        fn = system_fn_creg.invite(piece.system_fn)
        remote_peer, model = cls._resolve_model(peer_registry, model)
        return cls(partial_ref, rpc_call_factory, feed_factory, model, item_t, remote_peer, ctx, fn)

    def __init__(self, partial_ref, rpc_call_factory, feed_factory, model, item_t, remote_peer, ctx, fn):
        super().__init__(partial_ref, rpc_call_factory, feed_factory, model, item_t, remote_peer, ctx, fn)
        IndexTreeAdapterMixin.__init__(self, partial_ref)


class FnKeyTreeAdapter(FnTreeAdapter, KeyTreeAdapterMixin):

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx, partial_ref, system_fn_creg, rpc_call_factory, peer_registry, feed_factory):
        item_t = pyobj_creg.invite(piece.item_t)
        fn = system_fn_creg.invite(piece.system_fn)
        remote_peer, model = cls._resolve_model(peer_registry, model)
        key_field_t = pyobj_creg.invite(piece.key_field_t)
        return cls(partial_ref, rpc_call_factory, feed_factory,
                   model, item_t, remote_peer, ctx, fn, piece.key_field, key_field_t)

    def __init__(self, partial_ref, rpc_call_factory, feed_factory,
                 model, item_t, remote_peer, ctx, fn, key_field, key_field_t):
        super().__init__(partial_ref, rpc_call_factory, feed_factory, model, item_t, remote_peer, ctx, fn)
        KeyTreeAdapterMixin.__init__(self, partial_ref, key_field, key_field_t)


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
        key_field=piece.key_field,
        key_field_t=piece.key_field_t,
        system_fn=system_fn_ref,
        )
    return htypes.tree.view(mosaic.put(adapter))
