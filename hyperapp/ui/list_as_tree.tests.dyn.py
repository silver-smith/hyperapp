import logging
from unittest.mock import Mock

from . import htypes
from .services import (
    fn_to_ref,
    mosaic,
    pyobj_creg,
    )
from .code.context import Context
from .code.list_adapter import FnListAdapter
from .code.list_to_tree_adapter import ListToTreeAdapter
from .code.tree import TreeView
from .tested.code import list_as_tree

log = logging.getLogger(__name__)


def sample_list_fn(piece):
    log.info("Sample list fn: %s", piece)
    assert isinstance(piece, htypes.list_as_tree_tests.sample_list), repr(piece)
    return []


def test_switch_list_to_tree():
    ctx = Context()
    piece = htypes.list_as_tree_tests.sample_list()
    adapter_piece = htypes.list_adapter.fn_list_adapter(
        element_t=mosaic.put(pyobj_creg.reverse_resolve(htypes.list_as_tree_tests.item)),
        function=fn_to_ref(sample_list_fn),
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
