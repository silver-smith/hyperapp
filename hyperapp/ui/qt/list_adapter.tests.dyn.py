from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from . import htypes
from .services import (
    mosaic,
    types,
    )
from .tested.code import list_adapter


def test_static_adapter():
    value = [
        htypes.list_tests.item(1, "First"),
        htypes.list_tests.item(2, "Second"),
        htypes.list_tests.item(3, "Third"),
        ]
    t = deduce_complex_value_type(mosaic, types, value)
    piece = htypes.list_adapter.static_list_adapter(mosaic.put(value, t))
    adapter = list_adapter.StaticListAdapter.from_piece(piece)
    assert adapter.column_count() == 2
    assert adapter.row_count() == 3
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'title'
    assert adapter.cell_data(1, 0) == 2
    assert adapter.cell_data(2, 1) == "Third"


def test_fn_adapter():
    list_piece = htypes.sample_list.sample_list()
    adapter_piece = htypes.list_adapter.fn_list_adapter(mosaic.put(list_piece))
    adapter = list_adapter.FnListAdapter.from_piece(adapter_piece)
    assert adapter.column_count() == 2
    assert adapter.row_count() == 3
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'title'
    assert adapter.cell_data(1, 0) == 2
    assert adapter.cell_data(2, 1) == "Third sample"
