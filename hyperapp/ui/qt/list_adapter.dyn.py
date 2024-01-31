import logging
import weakref

from hyperapp.common.htypes import TList
from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from .services import (
    mosaic,
    pyobj_creg,
    types,
    web,
    )
from .code.list_diff import ListDiffAppend

log = logging.getLogger(__name__)


class StaticListAdapter:

    @classmethod
    def from_piece(cls, piece, ctx):
        value = web.summon(piece.value)
        list_t = deduce_complex_value_type(mosaic, types, value)
        assert isinstance(list_t, TList), repr(list_t)
        return cls(list_t.element_t, value)

    def __init__(self, item_t, value):
        self._item_t = item_t
        self._value = value  # record list.
        self._column_names = sorted(self._item_t.fields)

    def column_count(self):
        return len(self._item_t.fields)

    def column_title(self, column):
        return self._column_names[column]

    def row_count(self):
        return len(self._value)

    def cell_data(self, row, column):
        return getattr(self._value[row], self._column_names[column])

    def subscribe(self, model):
        pass


class _Feed:

    def __init__(self, adapter):
        self._adapter = adapter

    def send(self, diff):
        self._adapter.send_diff(diff)


class FnListAdapter:

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
        self._item_list = None
        self._subscribed_models = weakref.WeakSet()

    def column_count(self):
        return len(self._item_t.fields)

    def column_title(self, column):
        return self._column_names[column]

    def row_count(self):
        return len(self._items)

    def cell_data(self, row, column):
        item = self._items[row]
        return getattr(item, self._column_names[column])

    def subscribe(self, model):
        self._subscribed_models.add(model)

    def send_diff(self, diff):
        log.info("List adapter: send diff: %s", diff)
        if self._item_list is None:
            self._populate()
        if not isinstance(diff, ListDiffAppend):
            raise NotImplementedError(diff)
        self._item_list.append(diff.item)
        for model in self._subscribed_models:
            model.process_diff(diff)

    @property
    def _items(self):
        if self._item_list is not None:
            return self._item_list
        self._populate()
        return self._item_list

    def _populate(self):
        kw = {}
        if self._want_feed:
            kw['feed'] = _Feed(self)
        self._item_list = self._fn(self._model_piece, **kw)
