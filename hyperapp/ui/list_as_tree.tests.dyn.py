import logging
from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.context import Context
from .code.system_fn import ContextFn
from .code.model_command import UnboundModelCommand
from .code.list_adapter import list_model_state_t
from .code.list_as_tree_adapter import ListAsTreeAdapter
from .code.tree import TreeView
from .fixtures import feed_fixtures
from .tested.code import list_as_tree

log = logging.getLogger(__name__)


def sample_fn_1(piece):
    log.info("Sample fn 1: %s", piece)
    assert isinstance(piece, htypes.list_as_tree_tests.sample_list_1), repr(piece)
    return [
        htypes.list_as_tree_tests.item_1(0, "one", "First item"),
        htypes.list_as_tree_tests.item_1(1, "two", "Second item"),
        htypes.list_as_tree_tests.item_1(2, "three", "Third item"),
        ]


def test_switch_list_as_tree(ui_adapter_creg):
    ctx = Context()
    model = htypes.list_as_tree_tests.sample_list_1()
    fn_1 = htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_fn_1),
        ctx_params=('piece',),
        service_params=(),
        )
    piece = htypes.list_adapter.fn_list_adapter(
        item_t=pyobj_creg.actor_to_ref(htypes.list_as_tree_tests.item_1),
        system_fn=mosaic.put(fn_1),
        )
    adapter = ui_adapter_creg.animate(piece, model, ctx)

    view = Mock(adapter=adapter)
    hook = Mock()

    list_as_tree.switch_list_to_tree(model, view, hook, ctx)

    hook.replace_view.assert_called_once()
    new_view = hook.replace_view.call_args.args[0]
    assert isinstance(new_view, TreeView)
    assert isinstance(new_view.adapter, ListAsTreeAdapter)


def sample_fn_1_open(piece, current_item):
    log.info("Sample fn 1 open: %s", piece)
    assert isinstance(piece, htypes.list_as_tree_tests.sample_list_1), repr(piece)
    return htypes.list_as_tree_tests.sample_list_2(base_id=current_item.id)


def sample_fn_2_open(piece, current_item):
    log.info("Sample fn 2 open: %s", piece)
    assert isinstance(piece, htypes.list_as_tree_tests.sample_list_2), repr(piece)
    return htypes.list_as_tree_tests.sample_list_2(base_id=current_item.id)


@mark.config_fixture('model_command_reg')
def model_command_reg_config(partial_ref):
    open_fn_1 = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('piece', 'current_item'),
        service_params=(),
        unbound_fn=sample_fn_1_open,
        bound_fn=sample_fn_1_open,
        )
    open_fn_2 = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('piece', 'current_item'),
        service_params=(),
        unbound_fn=sample_fn_2_open,
        bound_fn=sample_fn_2_open,
        )
    command_1 = UnboundModelCommand(
        d=htypes.list_as_tree_tests.open_1_d(),
        ctx_fn=open_fn_1,
        properties=htypes.command.properties(False, False, False),
        )
    command_2 = UnboundModelCommand(
        d=htypes.list_as_tree_tests.open_2_d(),
        ctx_fn=open_fn_2,
        properties=htypes.command.properties(False, False, False),
        )
    return {
        htypes.list_as_tree_tests.sample_list_1: [command_1],
        htypes.list_as_tree_tests.sample_list_2: [command_2],
        }


@mark.fixture
def root_item_t():
    return pyobj_creg.actor_to_piece(htypes.list_as_tree_tests.item_1)


@mark.fixture
def fn_1():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(sample_fn_1),
        ctx_params=('piece',),
        service_params=(),
        )


@mark.fixture
def adapter_piece(data_to_ref, root_item_t, fn_1):
    open_command_1_d_ref = data_to_ref(htypes.list_as_tree_tests.open_1_d())
    return htypes.list_as_tree_adapter.adapter(
        root_item_t=mosaic.put(root_item_t),
        root_function=mosaic.put(fn_1),
        root_open_children_command_d=open_command_1_d_ref,
        layers=(),
        )


def test_open_opener_commands(ui_adapter_creg, adapter_piece):
    ctx = Context()
    model = htypes.list_as_tree_tests.sample_list_1()
    adapter = ui_adapter_creg.animate(adapter_piece, model, ctx)

    view = Mock(adapter=adapter)

    result = list_as_tree.open_opener_commands(view, current_path=[1])
    assert isinstance(result, htypes.list_as_tree.opener_commands), repr(result)
    assert web.summon(result.root_piece) == model
    assert web.summon(result.layer_piece) == model


@mark.fixture
def model_state():
    model_state_t = list_model_state_t(htypes.list_as_tree_tests.item_1)
    return model_state_t(
        current_idx=0,
        current_item=htypes.list_as_tree_tests.item_1(123, "some", "Some item"),
        )


def test_opener_commands_list(adapter_piece, model_state):
    ctx = Context()
    tree_view = htypes.tree.view(
        adapter=mosaic.put(adapter_piece),
        )
    lcs = Mock()
    lcs.get.return_value = tree_view
    root_piece = htypes.list_as_tree_tests.sample_list_1()
    layer_piece = htypes.list_as_tree_tests.sample_list_2(base_id=0)
    piece = htypes.list_as_tree.opener_commands(
        root_piece=mosaic.put(root_piece),
        layer_piece=mosaic.put(layer_piece),
        model_state=mosaic.put(model_state),
        )
    result = list_as_tree.opener_command_list(piece, lcs, ctx)
    assert type(result) is list
    assert len(result) == 1
    [item] = result
    assert item.name == 'open_2'
    assert pyobj_creg.invite_opt(item.command_d) == htypes.list_as_tree_tests.open_2_d()


async def test_set_root_open_command(data_to_ref, root_item_t, fn_1, model_state):
    ctx = Context()
    root_piece = htypes.list_as_tree_tests.sample_list_1()
    layer_piece = root_piece
    piece = htypes.list_as_tree.opener_commands(
        root_piece=mosaic.put(root_piece),
        layer_piece=mosaic.put(layer_piece),
        model_state=mosaic.put(model_state),
        )
    adapter_piece = htypes.list_as_tree_adapter.adapter(
        root_item_t=mosaic.put(root_item_t),
        root_function=mosaic.put(fn_1),
        root_open_children_command_d=None,
        layers=(),
        )
    view = htypes.tree.view(
        adapter=mosaic.put(adapter_piece),
        )
    current_item = htypes.list_as_tree.opener_command_item(
        command_d=data_to_ref(htypes.list_as_tree_tests.open_1_d()),
        name="<unused>",
        is_opener=False,
        )
    lcs = Mock()
    lcs.get.return_value = view
    result = await list_as_tree.toggle_open_command(piece, 0, current_item, ctx, lcs)
    lcs.set.assert_called_once()


async def test_set_non_root_open_command(data_to_ref, root_item_t, fn_1, model_state):
    ctx = Context()
    root_piece = htypes.list_as_tree_tests.sample_list_1()
    layer_piece_t = htypes.list_as_tree_tests.sample_list_2
    layer_piece = layer_piece_t(base_id=0)
    layer_piece_t_res = pyobj_creg.actor_to_piece(layer_piece_t)
    piece = htypes.list_as_tree.opener_commands(
        root_piece=mosaic.put(root_piece),
        layer_piece=mosaic.put(layer_piece),
        model_state=mosaic.put(model_state),
        )
    layers = (
        htypes.list_as_tree_adapter.layer(
            piece_t=mosaic.put(layer_piece_t_res),
            open_children_command_d=None,
            ),
        )
    adapter_piece = htypes.list_as_tree_adapter.adapter(
        root_item_t=mosaic.put(root_item_t),
        root_function=mosaic.put(fn_1),
        root_open_children_command_d=None,
        layers=layers,
        )
    view = htypes.tree.view(
        adapter=mosaic.put(adapter_piece),
        )
    current_item = htypes.list_as_tree.opener_command_item(
        command_d=data_to_ref(htypes.list_as_tree_tests.open_1_d()),
        name="<unused>",
        is_opener=False,
        )
    lcs = Mock()
    lcs.get.return_value = view
    result = await list_as_tree.toggle_open_command(piece, 0, current_item, ctx, lcs)
    lcs.set.assert_called_once()
