import logging

from . import htypes
from .services import (
    fn_to_ref,
    mark,
    model_command_factory,
    model_view_creg,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.list_adapter import FnListAdapter
from .code.list_to_tree_adapter import ListToTreeAdapter

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


@mark.ui_model_command(htypes.tree.view)
def open_opener_commands(view, current_path):
    adapter = view.adapter
    if not isinstance(adapter, ListToTreeAdapter):
        log.info("Not a ListToTreeAdapter: %r", adapter)
    piece = adapter.get_item_piece(current_path[:-1])
    return htypes.list_as_tree.opener_commands(
        model=mosaic.put(piece),
        )


def opener_command_list(piece):
    model = web.summon(piece.model)
    command_list = model_command_factory(model)
    return [
        htypes.list_as_tree.opener_command_item(
            command=mosaic.put(command),
            name=command.name,
            d=str(command.d),
            params=", ".join(command.params),
            )
        for command in command_list
        ]
