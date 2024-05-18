import logging

from . import htypes
from .services import (
    deduce_t,
    feed_factory,
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
from .code.list_diff import ListDiff
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
        return
    layer_piece = adapter.get_item_piece(current_path[:-1])
    return htypes.list_as_tree.opener_commands(
        root_piece=mosaic.put(adapter.model),
        layer_piece=mosaic.put(layer_piece),
        )


def _make_command_item(command, is_opener):
    return htypes.list_as_tree.opener_command_item(
        command=mosaic.put(command),
        name=command.name,
        d=str(command.d),
        params=", ".join(command.params),
        is_opener=is_opener,
        )


def _get_current_command(root_piece_t, layer_piece_t, adapter):
    if root_piece_t == layer_piece_t:
        return web.summon_opt(adapter.root_open_children_command)
    for layer in adapter.layers:
        t = pyobj_creg.invite(layer.piece_t)
        if t == layer_piece_t:
            return web.summon_opt(layer.open_children_command)
    # Layer is not yet included into adapter piece.
    return None


def _adjust_adapter(root_piece_t, layer_piece_t, adapter, new_command):
    new_command_ref = mosaic.put_opt(new_command)
    layers = list(adapter.layers)
    if root_piece_t == layer_piece_t:
        root_open_children_command = new_command_ref
    else:
        root_open_children_command = adapter.root_open_children_command
        for idx, layer in enumerate(adapter.layers):
            t = pyobj_creg.invite(layer.piece_t)
            if t == layer_piece_t:
                new_layer = htypes.list_to_tree_adapter.layer(
                    piece_t=layer.piece_t,
                    open_children_command=new_command_ref,
                    )
                layers[idx] = new_layer
                break
        else:
            piece_t_res = pyobj_creg.reverse_resolve(layer_piece_t)
            new_layer = htypes.list_to_tree_adapter.layer(
                piece_t=mosaic.put(piece_t_res),
                open_children_command=new_command_ref,
                )
            layers.append(new_layer)
    return htypes.list_to_tree_adapter.adapter(
        root_element_t=adapter.root_element_t,
        root_function=adapter.root_function,
        root_params=adapter.root_params,
        root_open_children_command=root_open_children_command,
        layers=tuple(layers),
        )


def opener_command_list(piece, lcs):
    root_piece, root_piece_t = web.summon_with_t(piece.root_piece)
    layer_piece, layer_piece_t = web.summon_with_t(piece.layer_piece)
    view = get_model_layout(lcs, root_piece_t)
    current_command = None
    if isinstance(view, htypes.tree.view):
        adapter = web.summon(view.adapter)
        if isinstance(adapter, htypes.list_to_tree_adapter.adapter):
            current_command = _get_current_command(root_piece_t, layer_piece_t, adapter)
    command_list = model_command_factory(layer_piece)
    return [
        _make_command_item(command, is_opener=command == current_command)
        for command in command_list
        ]


async def toggle_open_command(piece, current_idx, current_item, lcs):
    root_piece, root_piece_t = web.summon_with_t(piece.root_piece)
    layer_piece, layer_piece_t = web.summon_with_t(piece.layer_piece)
    view = get_model_layout(lcs, root_piece_t)
    if not isinstance(view, htypes.tree.view):
        log.info("View for %s is not a tree: %s", model_t, view)
        return
    adapter = web.summon(view.adapter)
    if not isinstance(adapter, htypes.list_to_tree_adapter.adapter):
        log.info("Adapter for %s is not a list-to-tree: %s", model_t, adapter)
        return
    prev_command = _get_current_command(root_piece_t, layer_piece_t, adapter)
    command_list = model_command_factory(layer_piece)
    prev_command_by_idx = {
        idx: cmd for idx, cmd
        in enumerate(command_list)
        if cmd == prev_command
        }
    new_command = web.summon(current_item.command)
    if new_command == prev_command:
        new_command = None
    new_adapter = _adjust_adapter(root_piece_t, layer_piece_t, adapter, new_command)
    new_view = htypes.tree.view(
        adapter=mosaic.put(new_adapter),
        )
    set_model_layout(lcs, root_piece_t, new_view)
    feed = feed_factory(piece)
    if prev_command_by_idx:
        idx, prev_command = next(iter(prev_command_by_idx.items()))
        prev_item = _make_command_item(prev_command, is_opener=False)
        await feed.send(ListDiff.Replace(idx, prev_item))
    current_command = web.summon(current_item.command)
    item = _make_command_item(current_command, is_opener=new_command is not None)
    await feed.send(ListDiff.Replace(current_idx, item))
