import logging
from unittest.mock import Mock

from . import htypes
from .services import (
    data_to_res,
    fn_to_ref,
    mark,
    mosaic,
    pyobj_creg,
    ui_adapter_creg,
    web,
    )
from .code.context import Context
from .code.list_adapter import FnListAdapter
from .code.list_to_tree_adapter import ListToTreeAdapter
from .code.tree import TreeView
from .tested.code import list_as_tree

log = logging.getLogger(__name__)


def sample_fn_1(piece):
    log.info("Sample fn 1: %s", piece)
    assert isinstance(piece, htypes.list_as_tree_tests.sample_list_1), repr(piece)
    return [
        htypes.list_to_tree_adapter_tests.item_1(0, "one", "First item"),
        htypes.list_to_tree_adapter_tests.item_1(1, "two", "Second item"),
        htypes.list_to_tree_adapter_tests.item_1(2, "three", "Third item"),
        ]


def test_switch_list_to_tree():
    ctx = Context()
    piece = htypes.list_as_tree_tests.sample_list_1()
    adapter_piece = htypes.list_adapter.fn_list_adapter(
        element_t=mosaic.put(pyobj_creg.reverse_resolve(htypes.list_as_tree_tests.item_1)),
        function=fn_to_ref(sample_fn_1),
        params=('piece',),
        )
    adapter = FnListAdapter.from_piece(adapter_piece, piece, ctx)

    view = Mock(adapter=adapter)
    hook = Mock()

    list_as_tree.switch_list_to_tree(piece, view, hook, ctx)

    hook.replace_view.assert_called_once()
    new_view = hook.replace_view.call_args.args[0]
    assert isinstance(new_view, TreeView)
    assert isinstance(new_view.adapter, ListToTreeAdapter)


def sample_fn_1_open(piece, current_item):
    log.info("Sample fn 1 open: %s", piece)
    assert isinstance(piece, htypes.list_as_tree_tests.sample_list_1), repr(piece)
    return htypes.list_as_tree_tests.sample_list_2(base_id=current_item.id)


def test_open_opener_commans():
    ctx = Context()
    model = htypes.list_as_tree_tests.sample_list_1()
    root_element_t = pyobj_creg.reverse_resolve(htypes.list_as_tree_tests.item_1)
    open_command_1_d_res = data_to_res(htypes.list_as_tree_tests.open_1_d())
    open_command_1_impl = htypes.ui.model_command_impl(
        function=fn_to_ref(sample_fn_1_open),
        params=('piece', 'current_item'),
        )
    open_command_1 = htypes.ui.model_command(
        d=mosaic.put(open_command_1_d_res),
        impl=mosaic.put(open_command_1_impl),
        )
    adapter_piece = htypes.list_to_tree_adapter.adapter(
        root_element_t=mosaic.put(root_element_t),
        root_function=fn_to_ref(sample_fn_1),
        root_params=('piece',),
        root_open_children_command=mosaic.put(open_command_1),
        layers=(),
        )
    adapter = ui_adapter_creg.animate(adapter_piece, model, ctx)

    view = Mock(adapter=adapter)

    result = list_as_tree.open_opener_commands(view, current_path=[1])
    assert isinstance(result, htypes.list_as_tree.opener_commands), repr(result)
    assert web.summon(result.root_piece) == model
    assert web.summon(result.layer_piece) == model


def _open_1_command():
    open_command_1_d_res = data_to_res(htypes.list_as_tree_tests.open_1_d())
    impl = htypes.ui.model_command_impl(
        function=fn_to_ref(sample_fn_1_open),
        params=('piece', 'current_item'),
        )
    return htypes.ui.model_command(
        d=mosaic.put(open_command_1_d_res),
        impl=mosaic.put(impl),
        )


@mark.service
def model_commands():
    def _factory(model):
        return [_open_1_command()]
    return _factory


def test_opener_commands_list():
    root_piece = htypes.list_as_tree_tests.sample_list_1()
    layer_piece = htypes.list_as_tree_tests.sample_list_2(base_id=0)
    piece = htypes.list_as_tree.opener_commands(
        root_piece=mosaic.put(root_piece),
        layer_piece=mosaic.put(layer_piece),
        )
    lcs = Mock()
    result = list_as_tree.opener_command_list(piece, lcs)
    assert type(result) is list
    item = result[0]
    assert item.name == 'open_1'
    assert web.summon(item.command) == _open_1_command()


async def test_non_root_open_command():
    root_piece = htypes.list_as_tree_tests.sample_list_1()
    layer_piece = root_piece
    piece = htypes.list_as_tree.opener_commands(
        root_piece=mosaic.put(root_piece),
        layer_piece=mosaic.put(layer_piece),
        )
    root_element_t = pyobj_creg.reverse_resolve(htypes.list_as_tree_tests.item_1)
    adapter_piece = htypes.list_to_tree_adapter.adapter(
        root_element_t=mosaic.put(root_element_t),
        root_function=fn_to_ref(sample_fn_1),
        root_params=('piece',),
        root_open_children_command=None,
        layers=(),
        )
    view = htypes.tree.view(
        adapter=mosaic.put(adapter_piece),
        )
    command = _open_1_command()
    current_item = htypes.list_as_tree.opener_command_item(
        command=mosaic.put(command),
        name='open_1',
        d=str(command.d),
        impl="<unused>",
        is_opener=False,
        )
    lcs = Mock()
    lcs.get.return_value = view
    result = await list_as_tree.toggle_open_command(piece, 0, current_item, lcs)
    lcs.set.assert_called_once()


async def test_set_non_root_open_command():
    root_piece = htypes.list_as_tree_tests.sample_list_1()
    layer_piece_t = htypes.list_as_tree_tests.sample_list_2
    layer_piece = layer_piece_t(base_id=0)
    layer_piece_t_res = pyobj_creg.reverse_resolve(layer_piece_t)
    piece = htypes.list_as_tree.opener_commands(
        root_piece=mosaic.put(root_piece),
        layer_piece=mosaic.put(layer_piece),
        )
    layers = (
        htypes.list_to_tree_adapter.layer(
            piece_t=mosaic.put(layer_piece_t_res),
            open_children_command=None,
            ),
        )
    root_element_t = pyobj_creg.reverse_resolve(htypes.list_as_tree_tests.item_1)
    adapter_piece = htypes.list_to_tree_adapter.adapter(
        root_element_t=mosaic.put(root_element_t),
        root_function=fn_to_ref(sample_fn_1),
        root_params=('piece',),
        root_open_children_command=None,
        layers=layers,
        )
    view = htypes.tree.view(
        adapter=mosaic.put(adapter_piece),
        )
    command = _open_1_command()
    current_item = htypes.list_as_tree.opener_command_item(
        command=mosaic.put(command),
        name="<unused>",
        d=str(command.d),
        impl="<unused>",
        is_opener=False,
        )
    lcs = Mock()
    lcs.get.return_value = view
    result = await list_as_tree.toggle_open_command(piece, 0, current_item, lcs)
    lcs.set.assert_called_once()
