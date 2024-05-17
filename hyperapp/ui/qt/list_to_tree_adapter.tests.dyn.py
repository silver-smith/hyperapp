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


def sample_fn_2_open(piece, current_item):
    log.info("Sample fn 2 open: %s", piece)
    assert isinstance(piece, htypes.list_to_tree_adapter_tests.sample_list_2), repr(piece)
    return htypes.list_to_tree_adapter_tests.sample_list_3(base_id=current_item.id)


def sample_fn_3(piece):
    log.info("Sample fn 3: %s", piece)
    assert isinstance(piece, htypes.list_to_tree_adapter_tests.sample_list_3), repr(piece)
    return [
        htypes.list_to_tree_adapter_tests.item_2(piece.base_id*10 + 0, "First item"),
        htypes.list_to_tree_adapter_tests.item_2(piece.base_id*10 + 1, "Second item"),
        htypes.list_to_tree_adapter_tests.item_2(piece.base_id*10 + 2, "Third item"),
        htypes.list_to_tree_adapter_tests.item_2(piece.base_id*10 + 3, "Fourth item"),
        ]


@mark.service
def pick_visualizer_info():
    def _pick_visualizer_info(t):
        if t is htypes.list_to_tree_adapter_tests.sample_list_2:
            element_t = pyobj_creg.reverse_resolve(htypes.list_to_tree_adapter_tests.item_2)
            ui_t = htypes.ui.list_ui_t(
                element_t=mosaic.put(element_t),
                )
            impl = htypes.ui.fn_impl(
                function=fn_to_ref(sample_fn_2),
                params=('piece',),
                )
            return (ui_t, impl)
        if t is htypes.list_to_tree_adapter_tests.sample_list_3:
            element_t = pyobj_creg.reverse_resolve(htypes.list_to_tree_adapter_tests.item_3)
            ui_t = htypes.ui.list_ui_t(
                element_t=mosaic.put(element_t),
                )
            impl = htypes.ui.fn_impl(
                function=fn_to_ref(sample_fn_3),
                params=('piece',),
                )
            return (ui_t, impl)
        assert False, repr(t)
    return _pick_visualizer_info


async def test_three_layers():
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
    open_command_2_d_res = data_to_res(htypes.list_to_tree_adapter_tests.open_2_d())
    open_command_2 = htypes.ui.model_command(
        d=(mosaic.put(open_command_2_d_res),),
        name='open_2',
        function=fn_to_ref(sample_fn_2_open),
        params=('piece', 'current_item'),
        )
    piece_2_t = pyobj_creg.reverse_resolve(htypes.list_to_tree_adapter_tests.sample_list_2)
    piece_3_t = pyobj_creg.reverse_resolve(htypes.list_to_tree_adapter_tests.sample_list_3)
    adapter_piece = htypes.list_to_tree_adapter.adapter(
        root_element_t=mosaic.put(root_element_t),
        root_function=fn_to_ref(sample_fn_1),
        root_params=('piece',),
        root_open_children_command=mosaic.put(open_command_1),
        layers=(
            htypes.list_to_tree_adapter.layer(
                piece_t=mosaic.put(piece_2_t),
                open_children_command=mosaic.put(open_command_2),
                ),
            htypes.list_to_tree_adapter.layer(
                piece_t=mosaic.put(piece_3_t),
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

    assert adapter.row_count(row_1_id) == 0
    return  # TODO

    assert adapter.row_count(row_1_id) == 4
    row_1_2_id = adapter.row_id(row_1_id, 2)
    assert adapter.cell_data(row_1_2_id, 0) == 12
    assert adapter.cell_data(row_1_2_id, 1) == "three"

    row_2_id = adapter.row_id(0, 2)
    assert adapter.row_count(row_2_id) == 4
    row_2_3_id = adapter.row_id(row_2_id, 3)
    assert adapter.cell_data(row_2_3_id, 0) == 23
    assert adapter.cell_data(row_2_3_id, 1) == "four"
    assert adapter.has_children(row_2_3_id)

    row_1_2_0_id = adapter.row_id(row_1_2_id, 0)
    assert adapter.cell_data(row_1_2_0_id, 0) == 120
    assert adapter.cell_data(row_1_2_0_id, 1) == "First item"
    assert not adapter.has_children(row_1_2_0_id)

    assert adapter.get_item_piece([]) == model
    assert adapter.get_item_piece([1]) == htypes.list_to_tree_adapter_tests.sample_list_2(1)
    assert adapter.get_item_piece([1, 2]) == htypes.list_to_tree_adapter_tests.sample_list_3(12)


async def test_single_layer():
    ctx = Context()
    model = htypes.list_to_tree_adapter_tests.sample_list_1()
    root_element_t = pyobj_creg.reverse_resolve(htypes.list_to_tree_adapter_tests.item_1)
    adapter_piece = htypes.list_to_tree_adapter.adapter(
        root_element_t=mosaic.put(root_element_t),
        root_function=fn_to_ref(sample_fn_1),
        root_params=('piece',),
        root_open_children_command=None,
        layers=(),
        )
    adapter = list_to_tree_adapter.ListToTreeAdapter.from_piece(adapter_piece, model, ctx)

    assert adapter.column_count() == 3
    assert adapter.column_title(0) == 'id'
    assert adapter.column_title(1) == 'name'
    assert adapter.column_title(2) == 'text'

    assert adapter.has_children(0)
    assert adapter.row_count(0) == 3
    row_1_id = adapter.row_id(0, 1)
    assert adapter.cell_data(row_1_id, 0) == 1
    assert adapter.cell_data(row_1_id, 1) == "two"
    assert adapter.cell_data(row_1_id, 2) == "Second item"

    assert not adapter.has_children(adapter.row_id(0, 0))
    assert not adapter.has_children(adapter.row_id(0, 1))
    assert not adapter.has_children(adapter.row_id(0, 2))
