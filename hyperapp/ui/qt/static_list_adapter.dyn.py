import logging

from hyperapp.common.htypes import TList

from . import htypes
from .services import (
    deduce_t,
    )
from .code.mark import mark
from .code.list_adapter import ListAdapterBase

log = logging.getLogger(__name__)


class StaticListAdapter(ListAdapterBase):

    @classmethod
    @mark.actor.ui_adapter_creg(htypes.list_adapter.static_list_adapter)
    def from_piece(cls, piece, model, ctx):
        list_t = deduce_t(model)
        assert isinstance(list_t, TList), repr(list_t)
        return cls(list_t.element_t, model)

    def __init__(self, item_t, value):
        self._item_t = item_t
        self._value = value  # record list.
        self._column_names = sorted(self._item_t.fields)

    def subscribe(self, model):
        pass

    @property
    def model(self):
        return self._value

    def column_count(self):
        return len(self._item_t.fields)

    def column_title(self, column):
        return self._column_names[column]

    def row_count(self):
        return len(self._value)

    def cell_data(self, row, column):
        return getattr(self._value[row], self._column_names[column])

    def get_item(self, idx):
        return self._value[idx]
