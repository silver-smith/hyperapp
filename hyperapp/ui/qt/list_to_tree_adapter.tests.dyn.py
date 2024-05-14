import logging

from . import htypes
from .services import (
    fn_to_ref,
    mosaic,
    pyobj_creg,
    )
from .code.context import Context
from .tested.code import list_to_tree_adapter

log = logging.getLogger(__name__)


def sample_fn_1(piece):
    log.info("Sample fn 1: %s", piece)
    assert isinstance(piece, htypes.list_to_tree_adapter_tests.sample_list_1), repr(piece)
    return [
        htypes.list_to_tree_adapter_tests.item_1(1, "one", "First item"),
        htypes.list_to_tree_adapter_tests.item_1(2, "two", "Second item"),
        htypes.list_to_tree_adapter_tests.item_1(3, "three", "Third item"),
        ]


def test_fn_adapter():
    ctx = Context()
    model = htypes.list_to_tree_adapter_tests.sample_list_1()
    root_element_t = pyobj_creg.reverse_resolve(htypes.list_to_tree_adapter_tests.item_1)
    adapter_piece = htypes.list_to_tree_adapter.adapter(
        root_element_t=mosaic.put(root_element_t),
        root_function=fn_to_ref(sample_fn_1),
        root_params=('piece',),
        layers=(),
        )
    adapter = list_to_tree_adapter.ListToTreeAdapter.from_piece(adapter_piece, model, ctx)

    assert adapter.column_count() == 3
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'name'
    assert adapter.column_title(2) == 'text'

    assert adapter.row_count(0) == 3
    row_1_id = adapter.row_id(0, 1)
    assert adapter.cell_data(row_1_id, 0) == 2
    assert adapter.cell_data(row_1_id, 1) == "two"
    assert adapter.cell_data(row_1_id, 2) == "Second item"

    # row_2_id = adapter.row_id(row_1_id, 2)
    # assert adapter.cell_data(row_2_id, 0) == 23
