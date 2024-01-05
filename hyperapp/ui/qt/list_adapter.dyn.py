from hyperapp.common.htypes import TList
from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from .services import (
    mosaic,
    pyobj_creg,
    types,
    web,
    )


class StaticListAdapter:

    @classmethod
    def from_piece(cls, piece):
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

    def row_count(self):
        return len(self._value)

    def column_title(self, column):
        return self._column_names[column]

    def cell_data(self, row, column):
        return getattr(self._value[row], self._column_names[column])


class FnListAdapter:

    @classmethod
    def from_piece(cls, piece):
        model_piece = web.summon(piece.model_piece)
        element_t = pyobj_creg.invite(piece.element_t)
        fn = pyobj_creg.invite(piece.function)
        value = fn(model_piece)
        return cls(element_t, value)

    def __init__(self, item_t, value):
        self._item_t = item_t
        self._value = value  # record list.
        self._column_names = sorted(self._item_t.fields)

    def column_count(self):
        return len(self._item_t.fields)

    def row_count(self):
        return len(self._value)

    def column_title(self, column):
        return self._column_names[column]

    def cell_data(self, row, column):
        return getattr(self._value[row], self._column_names[column])
