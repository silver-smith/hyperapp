import itertools
import logging
import weakref

from .services import (
    pyobj_creg,
    web,
    )
# from .code.list_diff import ListDiffAppend

log = logging.getLogger(__name__)


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
        self._id_to_item_list = {}
        self._id_to_children_id_list = {}
        self._id_to_parent_id = {}
        self._id_counter = itertools.count(start=1)
        self._subscribed_models = weakref.WeakSet()

    def column_count(self):
        return len(self._item_t.fields)

    def column_title(self, column):
        return self._column_names[column]

    def row_id(self, parent_id, row):
        try:
            row_ids = self._id_to_children_id_list[parent_id]
        except KeyError:
            self._populate(parent_id)
            row_ids = self._id_to_children_id_list[parent_id]
        return row_ids[row]

    def parent_id(self, id):
        if len(id) > 1:
            return id[:-1]
        else:
            return None

    def has_children(self, id):
        return self.row_count(id) > 0

    def row_count(self, parent_id):
        return len(self._items(parent_id))

    def cell_data(self, id, row, column):
        item = self._items(id)[row]
        return getattr(item, self._column_names[column])

    def subscribe(self, model):
        self._subscribed_models.add(model)

    # def send_diff(self, diff):
    #     log.info("List adapter: send diff: %s", diff)
    #     if self._item_list is None:
    #         self._populate()
    #     if not isinstance(diff, ListDiffAppend):
    #         raise NotImplementedError(diff)
    #     self._item_list.append(diff.item)
    #     for model in self._subscribed_models:
    #         model.process_diff(diff)

    def _items(self, parent_id):
        try:
            return self._id_to_item_list[parent_id]
        except IdError:
            pass
        self._populate(parent_id)
        return self._id_to_item_list[parent_id]

    def _populate(self, parent_id):
        kw = {}
        if self._want_feed:
            kw['feed'] = _Feed(self)
        if parent_id:
            parent_item
        items = self._fn(self._model_piece, parent_id, **kw)
        self._id_to_item_list[parent_id] = items
        self._id_to_children_id_list[parent_id] = [
            next(self._id_counter)
            for _ in items
            ]
        
