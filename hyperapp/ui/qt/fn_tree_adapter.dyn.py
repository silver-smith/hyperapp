import logging
from functools import cached_property

from hyperapp.boot.htypes import TList, TOptional, TRecord

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

    def __init__(self, rpc_call_factory, feed_factory, model, item_t, remote_peer, ctx, fn):
        super().__init__(model, item_t)
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
        if self._remote_peer:
            remote_peer = self._remote_peer
        else:
            try:
                remote_peer = self._ctx.remote_peer
            except KeyError:
                remote_peer = None
        if remote_peer:
            self._remote_populate(parent_id, remote_peer)
        else:
            self._local_populate(parent_id)

    def _local_populate(self, parent_id):
        kw = {
            'model': self._model,
            'piece': self._model,
            **self._parent_model_kw(parent_id),
            }
        item_list = self._fn.call(self._ctx, **kw)
        log.info("Fn tree adapter: retrieved local items for %s/%s: %s", self._model, parent_id, item_list)
        self._store_item_list(parent_id, item_list)

    def _remote_populate(self, parent_id, remote_peer):
        if parent_id != 0 and (pp_id := self._id_to_parent_id[parent_id]) in self._lateral_ids:
            grand_parent = self._id_to_item[pp_id]
            is_lateral = True
            lateral_parent_id = pp_id
            lateral_parent = self._id_to_item[pp_id]
        else:
            grand_parent = None
            is_lateral = False
            lateral_parent_id = parent_id
            lateral_parent = self._id_to_item[parent_id]
        item_list, lateral_item_list_list = self._call_servant_wrapper(
            receiver_peer=remote_peer,
            sender_identity=self._ctx.identity,
            ctx=self._ctx,
            fn=self._fn,
            model=self._model,
            grand_parent=grand_parent,
            is_lateral=is_lateral,
            lateral_parent=lateral_parent,
            **self._parent_model_kw(parent_id),
            )
        log.info("Fn tree adapter: retrieved remote items for %s/%s: %s", self._model, parent_id, item_list)
        if item_list:
            self._store_item_list(parent_id, item_list)
        lateral_id_list = self._id_to_children_id_list[lateral_parent_id]
        for idx, item_list in enumerate(lateral_item_list_list):
            item_id = lateral_id_list[idx]
            self._store_item_list(item_id, item_list)
            self._lateral_ids.add(item_id)

    @cached_property
    def _remote_result_t(self):
        item_t = self._item_t
        item_list_t = TList(item_t)
        return TRecord('ui_tree', f'remote_result_{item_t.module_name}_{item_t.name}', {
            'item_list': TOptional(item_list_t),
            'lateral_item_list_list': TList(item_list_t),
            })


class FnIndexTreeAdapter(FnTreeAdapter, IndexTreeAdapterMixin):

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx, rpc_system_call_factory, system_fn_creg, rpc_call_factory, peer_registry, feed_factory):
        item_t = pyobj_creg.invite(piece.item_t)
        fn = system_fn_creg.invite(piece.system_fn)
        remote_peer, model = cls._resolve_model(peer_registry, model)
        return cls(rpc_system_call_factory, rpc_call_factory, feed_factory, model, item_t, remote_peer, ctx, fn)

    def __init__(self, rpc_system_call_factory, rpc_call_factory, feed_factory, model, item_t, remote_peer, ctx, fn):
        super().__init__(rpc_call_factory, feed_factory, model, item_t, remote_peer, ctx, fn)
        IndexTreeAdapterMixin.__init__(self, rpc_system_call_factory)


class FnKeyTreeAdapter(FnTreeAdapter, KeyTreeAdapterMixin):

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx, rpc_system_call_factory, system_fn_creg, rpc_call_factory, peer_registry, feed_factory):
        item_t = pyobj_creg.invite(piece.item_t)
        fn = system_fn_creg.invite(piece.system_fn)
        remote_peer, model = cls._resolve_model(peer_registry, model)
        key_field_t = pyobj_creg.invite(piece.key_field_t)
        return cls(rpc_system_call_factory, rpc_call_factory, feed_factory,
                   model, item_t, remote_peer, ctx, fn, piece.key_field, key_field_t)

    def __init__(self, rpc_system_call_factory, rpc_call_factory, feed_factory,
                 model, item_t, remote_peer, ctx, fn, key_field, key_field_t):
        super().__init__(rpc_call_factory, feed_factory, model, item_t, remote_peer, ctx, fn)
        KeyTreeAdapterMixin.__init__(self, rpc_system_call_factory, key_field, key_field_t)


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
