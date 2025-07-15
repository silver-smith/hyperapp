import logging

from hyperapp.boot.htypes import TList

from . import htypes
from .services import (
    pyobj_creg,
    )
from .code.mark import mark
from .code.list_adapter import IndexListAdapterMixin

log = logging.getLogger(__name__)


class StaticListAdapter(IndexListAdapterMixin):

    @classmethod
    @mark.actor.ui_adapter_creg(htypes.list_adapter.static_list_adapter)
    def from_piece(cls, piece, model, ctx, accessor_creg):
        accessor = accessor_creg.invite(piece.accessor, model, ctx)
        item_t = pyobj_creg.invite(piece.item_t)
        return cls(item_t, accessor)

    def __init__(self, item_t, accessor):
        self._item_t = item_t
        self._accessor = accessor
        self._column_names = sorted(self._item_t.fields)

    def subscribe(self, model):
        pass

    @property
    def real_model(self):
        return None

    def column_count(self):
        return len(self._column_names)

    def column_title(self, column):
        return self._column_names[column]

    def row_count(self):
        return len(self._value)

    def cell_data(self, row, column):
        return getattr(self._value[row], self._column_names[column])

    def get_item(self, idx):
        return self._value[idx]

    @property
    def _value(self):
        return self._accessor.get_value()
