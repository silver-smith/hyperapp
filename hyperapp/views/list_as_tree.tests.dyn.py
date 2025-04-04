import logging
from unittest.mock import MagicMock, Mock

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
from .code.list_adapter import index_list_model_state_t
from .code.list_as_tree_adapter import ListAsTreeAdapter
from .code.tree import TreeView
from .fixtures import feed_fixtures
from .tested.code import list_as_tree

log = logging.getLogger(__name__)


def root_list_model(piece):
    log.info("Sample root model: %s", piece)
    assert isinstance(piece, htypes.list_as_tree_tests.sample_list_1), repr(piece)
    return [
        htypes.list_as_tree_tests.item_1(0, "one", "First item"),
        htypes.list_as_tree_tests.item_1(1, "two", "Second item"),
        htypes.list_as_tree_tests.item_1(2, "three", "Third item"),
        ]


@mark.fixture
def root_list_model_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(root_list_model),
        ctx_params=('piece',),
        service_params=(),
        )


def sample_fn_1_open(piece, current_item):
    log.info("Sample fn 1 open: %s", piece)
    assert isinstance(piece, htypes.list_as_tree_tests.sample_list_1), repr(piece)
    return htypes.list_as_tree_tests.sample_list_2(base_id=current_item.id)


def sample_fn_2_open(piece, current_item):
    log.info("Sample fn 2 open: %s", piece)
    assert isinstance(piece, htypes.list_as_tree_tests.sample_list_2), repr(piece)
    return htypes.list_as_tree_tests.sample_list_2(base_id=current_item.id)


@mark.fixture
def open_command_1(partial_ref):
    open_1_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('piece', 'current_item'),
        service_params=(),
        raw_fn=sample_fn_1_open,
        bound_fn=sample_fn_1_open,
        )
    return UnboundModelCommand(
        d=htypes.list_as_tree_tests.open_1_d(),
        ctx_fn=open_1_fn,
        properties=htypes.command.properties(False, False, False),
        )


@mark.fixture
def open_command_2(partial_ref):
    open_2_fn = ContextFn(
        partial_ref=partial_ref, 
        ctx_params=('piece', 'current_item'),
        service_params=(),
        raw_fn=sample_fn_2_open,
        bound_fn=sample_fn_2_open,
        )
    return UnboundModelCommand(
        d=htypes.list_as_tree_tests.open_2_d(),
        ctx_fn=open_2_fn,
        properties=htypes.command.properties(False, False, False),
        )


@mark.config_fixture('model_command_reg')
def model_command_reg_config(open_command_1, open_command_2):
    return {
        htypes.list_as_tree_tests.sample_list_1: [open_command_1],
        htypes.list_as_tree_tests.sample_list_2: [open_command_2],
        }


def test_ui_type_layout(root_list_model_fn):
    system_fn_ref = mosaic.put(root_list_model_fn)
    piece = htypes.model.list_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.list_as_tree_tests.item_1),
        )
    layout = list_as_tree.list_as_tree_ui_type_layout(piece, system_fn_ref)
    assert isinstance(layout, htypes.tree.view)


@mark.fixture
def root_model():
    return htypes.list_as_tree_tests.sample_list_1()


@mark.fixture
def ctx(root_model):
    return Context(
        model=root_model,
        )


def test_switch_list_as_tree(ui_adapter_creg, ctx, root_list_model_fn, root_model):
    piece = htypes.list_adapter.index_fn_list_adapter(
        item_t=pyobj_creg.actor_to_ref(htypes.list_as_tree_tests.item_1),
        system_fn=mosaic.put(root_list_model_fn),
        )
    adapter = ui_adapter_creg.animate(piece, root_model, ctx)

    view = Mock(adapter=adapter)
    hook = Mock()

    list_as_tree.switch_list_to_tree(root_model, view, hook, ctx)

    hook.replace_view.assert_called_once()
    new_view = hook.replace_view.call_args.args[0]
    assert isinstance(new_view, TreeView)
    assert isinstance(new_view.adapter, ListAsTreeAdapter)


@mark.fixture
def root_item_t():
    return pyobj_creg.actor_to_piece(htypes.list_as_tree_tests.item_1)


@mark.fixture
def adapter_piece(root_item_t, root_list_model_fn, open_command_1):
    return htypes.list_as_tree_adapter.adapter(
        root_item_t=mosaic.put(root_item_t),
        root_function=mosaic.put(root_list_model_fn),
        root_open_children_command=mosaic.put(open_command_1.piece),
        layers=(),
        )


def test_layer_list_model(open_command_1):
    layers = (
        htypes.list_as_tree_adapter.layer(
            piece_t=pyobj_creg.actor_to_ref(htypes.list_as_tree_tests.sample_list_2),
            open_children_command=None,
            ),
        )
    piece = htypes.list_as_tree.layer_list(
        root_piece_t=pyobj_creg.actor_to_ref(htypes.list_as_tree_tests.sample_list_1),
        root_open_children_command=mosaic.put(open_command_1.piece),
        layers=layers,
        )
    item_list = list_as_tree.list_as_tree_layers(piece)
    assert type(item_list) is list
    assert isinstance(item_list[0], htypes.list_as_tree.layer_list_item)


def test_open_layers(view_reg, ctx, adapter_piece, root_model):
    view_piece = htypes.tree.view(
        adapter=mosaic.put(adapter_piece),
        )
    view = view_reg.animate(view_piece, ctx)
    current_item = htypes.list_as_tree_tests.item_1(123, "some", "Some item"),
    piece = list_as_tree.open_layers(view, current_item, root_model)
    assert isinstance(piece, htypes.list_as_tree.layer_list)


def test_open_opener_commands(ui_adapter_creg, ctx, adapter_piece):
    model = htypes.list_as_tree_tests.sample_list_1()
    adapter = ui_adapter_creg.animate(adapter_piece, model, ctx)

    view = Mock(adapter=adapter)

    result = list_as_tree.open_opener_commands(view, current_path=[1])
    assert isinstance(result, htypes.list_as_tree.opener_commands), repr(result)
    assert web.summon(result.root_piece) == model
    assert web.summon(result.layer_piece) == model


@mark.fixture
def model_state():
    model_state_t = index_list_model_state_t(htypes.list_as_tree_tests.item_1)
    return model_state_t(
        current_idx=0,
        current_item=htypes.list_as_tree_tests.item_1(123, "some", "Some item"),
        )


def test_opener_commands_list(command_creg, ctx, adapter_piece, model_state):
    tree_view = htypes.tree.view(
        adapter=mosaic.put(adapter_piece),
        )
    root_piece = htypes.list_as_tree_tests.sample_list_1()
    layer_piece = htypes.list_as_tree_tests.sample_list_2(base_id=0)
    piece = htypes.list_as_tree.opener_commands(
        root_piece=mosaic.put(root_piece),
        layer_piece=mosaic.put(layer_piece),
        model_state=mosaic.put(model_state),
        )
    result = list_as_tree.opener_command_list(piece, ctx)
    assert type(result) is list
    assert len(result) == 1
    [item] = result
    assert item.name == 'Open 2', item.name
    assert command_creg.invite_opt(item.command).d == htypes.list_as_tree_tests.open_2_d()


@mark.fixture.obj
def model_layout_reg():
    return MagicMock()


async def test_set_root_open_command(model_layout_reg, ctx, open_command_1, root_item_t, root_list_model_fn, model_state):
    root_piece = htypes.list_as_tree_tests.sample_list_1()
    layer_piece = root_piece
    piece = htypes.list_as_tree.opener_commands(
        root_piece=mosaic.put(root_piece),
        layer_piece=mosaic.put(layer_piece),
        model_state=mosaic.put(model_state),
        )
    current_command = mosaic.put(open_command_1.piece)
    adapter_piece = htypes.list_as_tree_adapter.adapter(
        root_item_t=mosaic.put(root_item_t),
        root_function=mosaic.put(root_list_model_fn),
        root_open_children_command=None,
        layers=(),
        )
    view = htypes.tree.view(
        adapter=mosaic.put(adapter_piece),
        )
    model_layout_reg.get.return_value = view
    result = await list_as_tree.toggle_open_command(piece, current_command, ctx)
    model_layout_reg.__setitem__.assert_called_once()


async def test_set_non_root_open_command(model_layout_reg, ctx, open_command_1, root_item_t, root_list_model_fn, model_state):
    root_piece = htypes.list_as_tree_tests.sample_list_1()
    layer_piece_t = htypes.list_as_tree_tests.sample_list_2
    layer_piece = layer_piece_t(base_id=0)
    piece = htypes.list_as_tree.opener_commands(
        root_piece=mosaic.put(root_piece),
        layer_piece=mosaic.put(layer_piece),
        model_state=mosaic.put(model_state),
        )
    layers = (
        htypes.list_as_tree_adapter.layer(
            piece_t=pyobj_creg.actor_to_ref(layer_piece_t),
            open_children_command=None,
            ),
        )
    adapter_piece = htypes.list_as_tree_adapter.adapter(
        root_item_t=mosaic.put(root_item_t),
        root_function=mosaic.put(root_list_model_fn),
        root_open_children_command=None,
        layers=layers,
        )
    view = htypes.tree.view(
        adapter=mosaic.put(adapter_piece),
        )
    model_layout_reg.get.return_value = view
    current_command = mosaic.put(open_command_1.piece)
    result = await list_as_tree.toggle_open_command(piece, current_command, ctx)
    model_layout_reg.__setitem__.assert_called_once()
