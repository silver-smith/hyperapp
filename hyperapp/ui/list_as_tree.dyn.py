import logging

from . import htypes
from .services import (
    deduce_t,
    fn_to_ref,
    get_model_layout,
    set_model_layout,
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


def opener_command_list(piece, lcs):
    model, model_t = web.summon_with_t(piece.model)
    view = get_model_layout(lcs, model_t)
    current_command = None
    if isinstance(view, htypes.tree.view):
        adapter = web.summon(view.adapter)
        if isinstance(adapter, htypes.list_to_tree_adapter.adapter):
            if adapter.root_open_children_command is not None:
                current_command = web.summon(adapter.root_open_children_command)
    command_list = model_command_factory(model)
    return [
        htypes.list_as_tree.opener_command_item(
            command=mosaic.put(command),
            name=command.name,
            d=str(command.d),
            params=", ".join(command.params),
            is_opener=command == current_command,
            )
        for command in command_list
        ]


def toggle_use_command(piece, current_item, lcs):
    model, model_t = web.summon_with_t(piece.model)
    view = get_model_layout(lcs, model_t)
    if not isinstance(view, htypes.tree.view):
        log.info("View for %s is not a tree: %s", model_t, view)
    adapter = web.summon(view.adapter)
    if not isinstance(adapter, htypes.list_to_tree_adapter.adapter):
        log.info("Adapter for %s is not a list-to-tree: %s", model_t, adapter)
    if adapter.root_open_children_command == current_item.command:
        new_command = None
    else:
        new_command = current_item.command
    new_adapter = htypes.list_to_tree_adapter.adapter(
        root_element_t=adapter.root_element_t,
        root_function=adapter.root_function,
        root_params=adapter.root_params,
        root_open_children_command=new_command,
        layers=adapter.layers,
        )
    new_view = htypes.tree.view(
        adapter=mosaic.put(new_adapter),
        )
    set_model_layout(lcs, model_t, new_view)
