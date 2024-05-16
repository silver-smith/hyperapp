import logging

from . import htypes
from .services import (
    fn_to_ref,
    mark,
    model_view_creg,
    mosaic,
    pyobj_creg,
    )
from .code.list_adapter import FnListAdapter

log = logging.getLogger(__name__)


@mark.ui_command(htypes.list.view)
def switch_list_to_tree(piece, view, hook, ctx):
    list_adapter = view.adapter
    if not isinstance(list_adapter, FnListAdapter):
        log.info("Switch list to tree: Not an FnListAdapter: %r", list_adapter)
        return
    element_t_res = pyobj_creg.reverse_resolve(list_adapter.element_t)
    adapter = htypes.list_to_tree_adapter.adapter(
        root_element_t=mosaic.put(element_t_res),
        root_function=fn_to_ref(list_adapter.function),
        root_params=list_adapter.function_params,
        root_open_children_command=None,
        layers=(),
        )
    new_view_piece = htypes.tree.view(
        adapter=mosaic.put(adapter),
        )
    new_view = model_view_creg.animate(new_view_piece, piece, ctx)
    hook.replace_view(new_view)
