import logging
from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import tree_as_list

log = logging.getLogger(__name__)


def _tree_model(piece, current_path, parent):
    log.info("Sample tree model: %s, %s, %s", piece, current_path, parent)
    assert isinstance(piece, htypes.tree_as_list_tests.sample_tree_model), repr(piece)
    for idx in current_path:
        assert type(idx) is int
    if parent is not None:
        assert isinstance(parent, htypes.tree_as_list_tests.item)
        base = parent.id
    else:
        base = 0
    return [
        htypes.tree_as_list_tests.item(base*10 + 0, "one", "First item"),
        htypes.tree_as_list_tests.item(base*10 + 1, "two", "Second item"),
        htypes.tree_as_list_tests.item(base*10 + 2, "three", "Third item"),
        ]


@mark.fixture
def tree_model_fn():
    return htypes.system_fn.ctx_fn(
        function=pyobj_creg.actor_to_ref(_tree_model),
        ctx_params=('piece', 'current_path', 'parent'),
        service_params=(),
        )


@mark.fixture
def index_tree_ui_t():
    return htypes.model.index_tree_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.tree_as_list_tests.item),
        )


@mark.fixture
def key_tree_ui_t():
    return htypes.model.key_tree_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.tree_as_list_tests.item),
        key_field='id',
        key_field_t=pyobj_creg.actor_to_ref(htypes.builtin.int),
        )


@mark.fixture
def tree_model():
    return htypes.tree_as_list_tests.sample_tree_model()


@mark.fixture
def ctx(tree_model):
    return Context(
        model=tree_model,
        piece=tree_model,
        )


@mark.fixture
def index_view_piece(tree_model_fn, index_tree_ui_t):
    return tree_as_list.index_tree_as_list_ui_type_layout(index_tree_ui_t, mosaic.put(tree_model_fn))


@mark.fixture
def key_view_piece(tree_model_fn, key_tree_ui_t):
    return tree_as_list.key_tree_as_list_ui_type_layout(key_tree_ui_t, mosaic.put(tree_model_fn))
    

def test_index_ui_type_layout(index_view_piece):
    assert isinstance(index_view_piece, htypes.tree_as_list.view)
    

def test_key_ui_type_layout(key_view_piece):
    assert isinstance(key_view_piece, htypes.tree_as_list.view)


@mark.fixture
def index_wrapper_view(tree_model, index_view_piece, ctx):
    return tree_as_list.IndexTreeAsListWrapperView.from_piece(index_view_piece, tree_model, ctx)


@mark.fixture
def key_wrapper_view(tree_model, key_view_piece, ctx):
    return tree_as_list.KeyTreeAsListWrapperView.from_piece(key_view_piece, tree_model, ctx)


def test_index_view(index_view_piece, index_wrapper_view):
    assert index_wrapper_view.piece == index_view_piece


def test_key_view(key_view_piece, key_wrapper_view):
    assert key_wrapper_view.piece == key_view_piece


@mark.fixture
def run_open_command_test(tree_model, ctx, wrapper_view, current_path):
    hook = Mock()
    current_item = htypes.tree_as_list_tests.item(1, "two", "Second item")
    state = None
    tree_as_list.open(tree_model, current_path, current_item, wrapper_view, state, ctx, hook)
    hook.replace_view.assert_called_once()


def test_index_open_command(run_open_command_test, index_wrapper_view):
    run_open_command_test(index_wrapper_view, current_path=[1])


def test_key_open_command(run_open_command_test, key_wrapper_view):
    run_open_command_test(key_wrapper_view, current_path=[1])


@mark.fixture
def run_parent_command_test(view_reg, tree_model, ctx, wrapper_view, view_t):
    parent_item = htypes.tree_as_list_tests.item(1, "two", "Second item")
    child_view_piece = view_t(
        list_view=wrapper_view.piece.list_view,
        tree_model_fn=wrapper_view.piece.tree_model_fn,
        current_path=(mosaic.put(2),),
        parent_items=(mosaic.put(parent_item),),
        )
    child_view = view_reg.animate(child_view_piece, ctx)
    hook = Mock()
    state = None
    tree_as_list.parent(tree_model, child_view, state, ctx, hook)
    hook.replace_view.assert_called_once()


def test_index_parent_command(run_parent_command_test, index_wrapper_view):
    run_parent_command_test(index_wrapper_view, htypes.tree_as_list.index_view)


def test_key_parent_command(run_parent_command_test, key_wrapper_view):
    run_parent_command_test(key_wrapper_view, htypes.tree_as_list.key_view)
