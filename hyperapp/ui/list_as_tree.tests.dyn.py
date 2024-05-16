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
    open_command_1 = htypes.ui.model_command(
        d=(mosaic.put(open_command_1_d_res),),
        name='open_1',
        function=fn_to_ref(sample_fn_1_open),
        params=('piece', 'current_item'),
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
    assert isinstance(result, htypes.list_as_tree.opener_commands)
    assert web.summon(result.model) == model


def _open_1_command():
    open_command_1_d_res = data_to_res(htypes.list_as_tree_tests.open_1_d())
    return htypes.ui.model_command(
        d=(mosaic.put(open_command_1_d_res),),
        name='open_1',
        function=fn_to_ref(sample_fn_1_open),
        params=('piece', 'current_item'),
        )


@mark.service
def model_command_factory():
    def _factory(model):
        return [_open_1_command()]
    return _factory


def test_opener_commands_list():
    model = htypes.list_as_tree_tests.sample_list_1()
    piece = htypes.list_as_tree.opener_commands(
        model=mosaic.put(model),
        )
    result = list_as_tree.opener_command_list(piece)
    assert type(result) is list
    item = result[0]
    assert item.name == 'open_1'
    assert web.summon(item.command) == _open_1_command()
