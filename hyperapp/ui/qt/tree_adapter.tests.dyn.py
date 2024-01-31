from hyperapp.common.htypes import tInt

from . import htypes
from .services import (
    fn_to_ref,
    mosaic,
    pyobj_creg,
    )
from .code.context import Context
# from .code.list_diff import ListDiffAppend
from .tested.code import tree_adapter


def sample_tree_fn(piece, parent):
    assert isinstance(piece, htypes.tree_adapter_tests.sample_tree), repr(piece)
    if parent:
        base = parent.id
    else:
        base = 0
    return [
        htypes.tree_adapter_tests.item(base*10 + 1, "First item"),
        htypes.tree_adapter_tests.item(base*10 + 2, "Second item"),
        htypes.tree_adapter_tests.item(base*10 + 3, "Third item"),
        ]


def test_fn_adapter():
    ctx = Context()
    model_piece = htypes.tree_adapter_tests.sample_tree()
    adapter_piece = htypes.tree_adapter.fn_index_tree_adapter(
        model_piece=mosaic.put(model_piece),
        element_t=mosaic.put(pyobj_creg.reverse_resolve(htypes.tree_adapter_tests.item)),
        key_t=mosaic.put(pyobj_creg.reverse_resolve(tInt)),
        function=fn_to_ref(sample_tree_fn),
        want_feed=False,
        )
    adapter = tree_adapter.FnIndexTreeAdapter.from_piece(adapter_piece, ctx)
    assert adapter.column_count() == 2
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'text'
    assert adapter.row_count(0) == 3
    assert adapter.cell_data(0, 1, 0) == 2
    assert adapter.cell_data(0, 2, 1) == "Third item"
    parent_id = adapter.row_id(0, 2)
    assert adapter.cell_data(parent_id, 1, 0) == 32
