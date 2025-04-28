from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.context import Context
from .tested.code import tree_as_list


def tree_model(piece, current_path, parent):
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
        function=pyobj_creg.actor_to_ref(tree_model),
        ctx_params=('piece', 'current_path', 'parent'),
        service_params=(),
        )


@mark.fixture
def tree_ui_t():
    return htypes.model.index_tree_ui_t(
        item_t=pyobj_creg.actor_to_ref(htypes.tree_as_list_tests.item),
        )


@mark.fixture
def ctx():
    return Context()


def test_view(tree_model_fn, tree_ui_t, ctx):
    model = htypes.tree_as_list_tests.sample_tree_model()
    piece = tree_as_list.index_tree_as_list_ui_type_layout(tree_ui_t, mosaic.put(tree_model_fn))
    view = tree_as_list.TreeAsListWrapperView.from_piece(piece, model, ctx)
    assert view.piece == piece
    

def test_index_ui_type_layout(tree_model_fn, tree_ui_t):
    layout = tree_as_list.index_tree_as_list_ui_type_layout(tree_ui_t, mosaic.put(tree_model_fn))
    assert isinstance(layout, htypes.tree_as_list.view)
