import logging

from . import htypes
from .services import (
    data_to_res,
    fn_to_ref,
    mark,
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
        htypes.list_to_tree_adapter_tests.item_1(0, "one", "First item"),
        htypes.list_to_tree_adapter_tests.item_1(1, "two", "Second item"),
        htypes.list_to_tree_adapter_tests.item_1(2, "three", "Third item"),
        ]


def sample_fn_1_open(piece, current_item):
    log.info("Sample fn 1 open: %s", piece)
    assert isinstance(piece, htypes.list_to_tree_adapter_tests.sample_list_1), repr(piece)
    return htypes.list_to_tree_adapter_tests.sample_list_2(base_id=current_item.id)


def sample_fn_2(piece):
    log.info("Sample fn 2: %s", piece)
    assert isinstance(piece, htypes.list_to_tree_adapter_tests.sample_list_2), repr(piece)
    return [
        htypes.list_to_tree_adapter_tests.item_2(piece.base_id*10 + 0, "one"),
        htypes.list_to_tree_adapter_tests.item_2(piece.base_id*10 + 1, "two"),
        htypes.list_to_tree_adapter_tests.item_2(piece.base_id*10 + 2, "three"),
        htypes.list_to_tree_adapter_tests.item_2(piece.base_id*10 + 3, "four"),
        ]


@mark.service
def pick_visualizer_info():
    def _pick_visualizer_info(t):
        assert t is htypes.list_to_tree_adapter_tests.sample_list_2, repr(t)
        element_t = pyobj_creg.reverse_resolve(htypes.list_to_tree_adapter_tests.item_2)
        ui_t = htypes.ui.list_ui_t(
            element_t=mosaic.put(element_t),
            )
        impl = htypes.ui.fn_impl(
            function=fn_to_ref(sample_fn_2),
            params=('piece',),
            )
        return (ui_t, impl)
    return _pick_visualizer_info


def test_fn_adapter():
    ctx = Context()
    model = htypes.list_to_tree_adapter_tests.sample_list_1()
    root_element_t = pyobj_creg.reverse_resolve(htypes.list_to_tree_adapter_tests.item_1)
    open_command_1_d_res = data_to_res(htypes.list_to_tree_adapter_tests.open_1_d())
    open_command_1 = htypes.ui.model_command(
        d=(mosaic.put(open_command_1_d_res),),
        name='open_1',
        function=fn_to_ref(sample_fn_1_open),
        params=('piece', 'current_item'),
        )
    piece_2_t = pyobj_creg.reverse_resolve(htypes.list_to_tree_adapter_tests.sample_list_2)
    adapter_piece = htypes.list_to_tree_adapter.adapter(
        root_element_t=mosaic.put(root_element_t),
        root_function=fn_to_ref(sample_fn_1),
        root_params=('piece',),
        root_open_children_command=mosaic.put(open_command_1),
        layers=(
            htypes.list_to_tree_adapter.layer(
                piece_t=mosaic.put(piece_2_t),
                open_children_command=None,
                ),
            ),
        )
    adapter = list_to_tree_adapter.ListToTreeAdapter.from_piece(adapter_piece, model, ctx)

    assert adapter.column_count() == 3
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'name'
    assert adapter.column_title(2) == 'text'

    assert adapter.row_count(0) == 3
    row_1_id = adapter.row_id(0, 1)
    assert adapter.cell_data(row_1_id, 0) == 1
    assert adapter.cell_data(row_1_id, 1) == "two"
    assert adapter.cell_data(row_1_id, 2) == "Second item"

    assert adapter.row_count(row_1_id) == 4
    row_1_2_id = adapter.row_id(row_1_id, 2)
    assert adapter.cell_data(row_1_2_id, 0) == 12
    assert adapter.cell_data(row_1_2_id, 1) == "three"

    row_2_id = adapter.row_id(0, 2)
    assert adapter.row_count(row_2_id) == 4
    row_2_3_id = adapter.row_id(row_2_id, 3)
    assert adapter.cell_data(row_2_3_id, 0) == 23
    assert adapter.cell_data(row_2_3_id, 1) == "four"
