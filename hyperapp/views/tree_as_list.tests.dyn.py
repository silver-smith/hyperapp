from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import tree_as_list


def _tree_model(piece, current_path, parent):
    log.info("Sample tree model: %s, %s, %s", piece, current_path, parent_item)
    assert isinstance(piece, htypes.tree_as_list_tests.sample_tree_model), repr(piece)
    for idx in current_path:
        assert type(idx) is int
    if parent_item is not None:
        assert isinstance(parent_item, htypes.tree_as_list_tests.item)
        base = parent_item.id
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
def tree_ui_t():
    return htypes.model.index_tree_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.tree_as_list_tests.item),
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
def view_piece(tree_model_fn, tree_ui_t):
    return tree_as_list.index_tree_as_list_ui_type_layout(tree_ui_t, mosaic.put(tree_model_fn))
    

def test_index_ui_type_layout(view_piece):
    assert isinstance(view_piece, htypes.tree_as_list.view)


@mark.fixture
def wrapper_view(tree_model_fn, view_piece, ctx):
    model = htypes.tree_as_list_tests.sample_tree_model()
    return tree_as_list.TreeAsListWrapperView.from_piece(view_piece, model, ctx)


def test_view(view_piece, wrapper_view):
    assert wrapper_view.piece == view_piece


def test_open_command(tree_model_fn, tree_model, ctx, wrapper_view):
    hook = Mock()
    current_idx = 1
    current_item = htypes.tree_as_list_tests.item(1, "two", "Second item")
    state = None
    tree_as_list.open(tree_model, current_idx, current_item, wrapper_view, state, ctx, hook)
    hook.replace_view.assert_called_once()


def test_parent_command(view_reg, tree_model, ctx, wrapper_view):
    parent_item = htypes.tree_as_list_tests.item(1, "two", "Second item")
    child_view_piece = htypes.tree_as_list.view(
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
