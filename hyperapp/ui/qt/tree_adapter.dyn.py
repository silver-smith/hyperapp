import abc
import itertools
import logging
import weakref

from .services import (
    feed_factory,
    peer_registry,
    pyobj_creg,
    rpc_call_factory,
    web,
    )
from .code.tree_diff import TreeDiff
from .code.tree import VisualTreeDiffAppend, VisualTreeDiffInsert

log = logging.getLogger(__name__)


class FnIndexTreeAdapterBase(metaclass=abc.ABCMeta):

    def __init__(self, model_piece, item_t, want_feed):
        self._model_piece = model_piece
        self._item_t = item_t
        self._want_feed = want_feed
        self._column_names = sorted(self._item_t.fields)
        self._id_to_item = {}
        self._id_to_children_id_list = {}
        self._id_to_parent_id = {}
        self._id_counter = itertools.count(start=1)
        self._subscribers = weakref.WeakSet()
        self._feed = feed_factory(model_piece)
        self._feed.subscribe(self)

    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)

    @property
    def model(self):
        return self._model_piece

    def column_count(self):
        return len(self._item_t.fields)

    def column_title(self, column):
        return self._column_names[column]

    def row_id(self, parent_id, row):
        return self._id_list(parent_id)[row]

    def parent_id(self, id):
        if id == 0:
            return 0
        else:
            return self._id_to_parent_id[id]

    def has_children(self, id):
        return self.row_count(id) > 0

    def row_count(self, parent_id):
        id_list = self._id_list(parent_id)
        return len(id_list)

    def cell_data(self, id, column):
        item = self._id_to_item[id]
        return getattr(item, self._column_names[column])

    def get_item(self, id):
        return self._id_to_item.get(id)

    def process_diff(self, diff):
        log.info("Tree adapter: process diff: %s", diff)
        if not isinstance(diff, (TreeDiff.Append, TreeDiff.Insert)):
            raise NotImplementedError(diff)
        parent_id = 0
        if isinstance(diff, TreeDiff.Append):
            parent_path = diff.path
        else:
            parent_path = diff.path[:-1]
        for idx in parent_path:
            if parent_id not in self._id_to_children_id_list:
                self._populate(parent_id)
            parent_id = self._id_to_children_id_list[parent_id][idx]
        item_id = next(self._id_counter)
        self._id_to_item[item_id] = diff.item
        self._id_to_parent_id[item_id] = parent_id
        if isinstance(diff, TreeDiff.Append):
            self._id_to_children_id_list[parent_id].append(item_id)
            visual_diff = VisualTreeDiffAppend(parent_id)
        else:
            idx = diff.path[-1]
            self._id_to_children_id_list[parent_id].insert(idx, item_id)
            visual_diff = VisualTreeDiffInsert(parent_id, idx)
        for subscriber in self._subscribers:
            subscriber.process_diff(visual_diff)

    def _id_list(self, parent_id):
        try:
            return self._id_to_children_id_list[parent_id]
        except KeyError:
            return self._populate(parent_id)
            return self._id_to_children_id_list[parent_id]

    def _populate(self, parent_id):
        if parent_id:
            parent_item = self._id_to_item[parent_id]  # Expecting upper level is already populated.
        else:
            parent_item = None
        kw = {
            'piece': self._model_piece,
            'parent': parent_item,
            }
        if self._want_feed:
            kw['feed'] = self._feed
        item_list = self._call_fn(**kw)
        log.info("Tree adapter: populated (%s, %s) -> %s", self._model_piece, parent_item, item_list)
        item_id_list = []
        for item in item_list:
            id = next(self._id_counter)
            item_id_list.append(id)
            self._id_to_item[id] = item
            self._id_to_parent_id[id] = parent_id
        self._id_to_children_id_list[parent_id] = item_id_list
        return item_id_list

    @abc.abstractmethod
    def _call_fn(self, **kw):
        pass


class FnIndexTreeAdapter(FnIndexTreeAdapterBase):

    @classmethod
    def from_piece(cls, piece, ctx):
        model_piece = web.summon(piece.model_piece)
        element_t = pyobj_creg.invite(piece.element_t)
        fn = pyobj_creg.invite(piece.function)
        return cls(model_piece, element_t, piece.want_feed, fn)

    def __init__(self, model_piece, item_t, want_feed, fn):
        super().__init__(model_piece, item_t, want_feed)
        self._fn = fn

    def _call_fn(self, **kw):
        return self._fn(**kw)


class RemoteFnIndexTreeAdapter(FnIndexTreeAdapterBase):

    @classmethod
    def from_piece(cls, piece, ctx):
        model_piece = web.summon(piece.model_piece)
        element_t = pyobj_creg.invite(piece.element_t)
        remote_peer = peer_registry.invite(piece.remote_peer)
        return cls(model_piece, element_t, piece.want_feed, piece.function, ctx.rpc_endpoint, ctx.identity, remote_peer)

    def __init__(self, model_piece, item_t, want_feed, fn_res_ref, rpc_endpoint, identity, remote_peer):
        super().__init__(model_piece, item_t, want_feed)
        self._rpc_call = rpc_call_factory(
            rpc_endpoint=rpc_endpoint,
            receiver_peer=remote_peer,
            servant_ref=fn_res_ref,
            sender_identity=identity,
            )

    def _call_fn(self, **kw):
        return self._rpc_call(**kw)
