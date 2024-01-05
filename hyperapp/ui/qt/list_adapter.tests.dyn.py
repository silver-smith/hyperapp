from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

from . import htypes
from .services import (
    fn_to_ref,
    mosaic,
    pyobj_creg,
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


def sample_list_fn(piece):
    assert isinstance(piece, htypes.list_adapter_tests.sample_list), repr(piece)
    return [
        htypes.list_adapter_tests.item(11, "First item"),
        htypes.list_adapter_tests.item(22, "Second item"),
        htypes.list_adapter_tests.item(33, "Third item"),
        ]


def test_fn_adapter():
    model_piece = htypes.list_adapter_tests.sample_list()
    adapter_piece = htypes.list_adapter.fn_list_adapter(
        model_piece=mosaic.put(model_piece),
        element_t=mosaic.put(pyobj_creg.reverse_resolve(htypes.list_adapter_tests.item)),
        function=fn_to_ref(sample_list_fn),
        )
    adapter = list_adapter.FnListAdapter.from_piece(adapter_piece)
    assert adapter.column_count() == 2
    assert adapter.row_count() == 3
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'text'
    assert adapter.cell_data(1, 0) == 22
    assert adapter.cell_data(2, 1) == "Third item"
