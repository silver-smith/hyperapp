import itertools
import logging
import weakref

from .services import (
    pyobj_creg,
    web,
    )
from .code.tree_diff import TreeDiffAppend
from .code.tree import VisualTreeDiffAppend

log = logging.getLogger(__name__)


class _Feed:

    def __init__(self, adapter):
        self._adapter = adapter

    def send(self, diff):
        self._adapter.send_diff(diff)


class FnIndexTreeAdapter:

    @classmethod
    def from_piece(cls, piece, ctx):
        model_piece = web.summon(piece.model_piece)
        element_t = pyobj_creg.invite(piece.element_t)
        fn = pyobj_creg.invite(piece.function)
        return cls(model_piece, element_t, piece.want_feed, fn)

    def __init__(self, model_piece, item_t, want_feed, fn):
        self._model_piece = model_piece
        self._item_t = item_t
        self._want_feed = want_feed
        self._fn = fn
        self._column_names = sorted(self._item_t.fields)
        self._id_to_item = {}
        self._id_to_children_id_list = {}
        self._id_to_parent_id = {}
        self._id_counter = itertools.count(start=1)
        self._subscribed_models = weakref.WeakSet()

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

    def subscribe(self, model):
        self._subscribed_models.add(model)

    def send_diff(self, diff):
        log.info("Tree adapter: send diff: %s", diff)
        if not isinstance(diff, TreeDiffAppend):
            raise NotImplementedError(diff)
        parent_id = 0
        for idx in diff.path:
            if parent_id not in self._id_to_children_id_list:
                self._populate(parent_id)
            parent_id = self._id_to_children_id_list[parent_id][idx]
        item_id = next(self._id_counter)
        self._id_to_item[item_id] = diff.item
        self._id_to_parent_id[item_id] = parent_id
        self._id_to_children_id_list[parent_id].append(item_id)
        visual_diff = VisualTreeDiffAppend(parent_id)
        for model in self._subscribed_models:
            model.process_diff(visual_diff)

    def _id_list(self, parent_id):
        try:
            return self._id_to_children_id_list[parent_id]
        except KeyError:
            return self._populate(parent_id)
            return self._id_to_children_id_list[parent_id]

    def _populate(self, parent_id):
        kw = {}
        if self._want_feed:
            kw['feed'] = _Feed(self)
        if parent_id:
            parent_item = self._id_to_item[parent_id]  # Expecting upper level is already populated.
        else:
            parent_item = None
        item_list = self._fn(self._model_piece, parent_item, **kw)
        log.info("Tree adapter: populated %s (%s, %s) -> %s", self._fn.__name__, self._model_piece, parent_item, item_list)
        item_id_list = []
        for item in item_list:
            id = next(self._id_counter)
            item_id_list.append(id)
            self._id_to_item[id] = item
            self._id_to_parent_id[id] = parent_id
        self._id_to_children_id_list[parent_id] = item_id_list
        return item_id_list
