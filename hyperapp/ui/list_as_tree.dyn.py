import logging

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.directory import d_to_name
from .code.list_diff import ListDiff
from .code.fn_list_adapter import FnListAdapter
from .code.list_as_tree_adapter import ListAsTreeAdapter
from .code.model_command import model_command_ctx

log = logging.getLogger(__name__)


@mark.ui_command(htypes.list.view)
def switch_list_to_tree(piece, view, hook, ctx, model_view_creg):
    list_adapter = view.adapter
    if not isinstance(list_adapter, FnListAdapter):
        log.info("Switch list to tree: Not an FnListAdapter: %r", list_adapter)
        return
    item_t_res = pyobj_creg.actor_to_piece(list_adapter.item_t)
    adapter = htypes.list_as_tree_adapter.adapter(
        root_item_t=mosaic.put(item_t_res),
        root_function=mosaic.put(list_adapter.function.piece),
        root_open_children_command_d=None,
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
    if not isinstance(adapter, ListAsTreeAdapter):
        log.info("Not a ListAsTreeAdapter: %r", adapter)
        return
    layer_piece = adapter.get_item_piece(current_path[:-1])
    model_state = adapter.get_item_list_model_state(current_path)
    return htypes.list_as_tree.opener_commands(
        root_piece=mosaic.put(adapter.model),
        layer_piece=mosaic.put(layer_piece),
        model_state=mosaic.put(model_state),
        )


def _make_command_item(data_to_ref, command, is_opener):
    return htypes.list_as_tree.opener_command_item(
        command_d=data_to_ref(command.d),
        name=d_to_name(command.d),
        is_opener=is_opener,
        )


def _get_current_command_d(root_piece_t, layer_piece_t, adapter):
    if root_piece_t == layer_piece_t:
        return pyobj_creg.invite_opt(adapter.root_open_children_command_d)
    for layer in adapter.layers:
        t = pyobj_creg.invite(layer.piece_t)
        if t == layer_piece_t:
            return pyobj_creg.invite_opt(layer.open_children_command_d)
    # Layer is not yet included into adapter piece.
    return None


def _amend_adapter(data_to_ref, root_piece_t, layer_piece_t, adapter, new_command_d):
    if new_command_d is None:
        new_command_d_ref = None
    else:
        new_command_d_ref = data_to_ref(new_command_d)
    layers = list(adapter.layers)
    if root_piece_t == layer_piece_t:
        root_open_children_command_d = new_command_d_ref
    else:
        root_open_children_command_d = adapter.root_open_children_command_d
        for idx, layer in enumerate(adapter.layers):
            t = pyobj_creg.invite(layer.piece_t)
            if t == layer_piece_t:
                new_layer = htypes.list_as_tree_adapter.layer(
                    piece_t=layer.piece_t,
                    open_children_command_d=new_command_d_ref,
                    )
                layers[idx] = new_layer
                break
        else:
            piece_t_res = pyobj_creg.actor_to_piece(layer_piece_t)
            new_layer = htypes.list_as_tree_adapter.layer(
                piece_t=mosaic.put(piece_t_res),
                open_children_command_d=new_command_d_ref,
                )
            layers.append(new_layer)
    return htypes.list_as_tree_adapter.adapter(
        root_item_t=adapter.root_item_t,
        root_function=adapter.root_function,
        root_open_children_command_d=root_open_children_command_d,
        layers=tuple(layers),
        )


@mark.model
def opener_command_list(piece, lcs, ctx, data_to_ref, get_model_commands, get_custom_layout):
    root_piece, root_piece_t = web.summon_with_t(piece.root_piece)
    layer_piece, layer_piece_t = web.summon_with_t(piece.layer_piece)
    model_state = web.summon(piece.model_state)
    view = get_custom_layout(lcs, root_piece_t)
    current_command_d = None
    if isinstance(view, htypes.tree.view):
        adapter = web.summon(view.adapter)
        if isinstance(adapter, htypes.list_as_tree_adapter.adapter):
            current_command_d = _get_current_command_d(root_piece_t, layer_piece_t, adapter)
    command_ctx = model_command_ctx(ctx, layer_piece, model_state)
    command_list = get_model_commands(layer_piece_t, command_ctx)
    return [
        _make_command_item(data_to_ref, command, is_opener=command.d == current_command_d)
        for command in command_list
        ]


@mark.command
async def toggle_open_command(
        piece, current_idx, current_item, ctx, lcs,
        data_to_ref, feed_factory, get_model_commands, get_custom_layout, set_custom_layout):
    root_piece, root_piece_t = web.summon_with_t(piece.root_piece)
    layer_piece, layer_piece_t = web.summon_with_t(piece.layer_piece)
    model_state = web.summon(piece.model_state)
    view = get_custom_layout(lcs, root_piece_t)
    if not isinstance(view, htypes.tree.view):
        log.info("View for %s is not a tree: %s", model_t, view)
        return
    adapter = web.summon(view.adapter)
    if not isinstance(adapter, htypes.list_as_tree_adapter.adapter):
        log.info("Adapter for %s is not a list-to-tree: %s", model_t, adapter)
        return
    prev_command_d = _get_current_command_d(root_piece_t, layer_piece_t, adapter)
    command_ctx = model_command_ctx(ctx, layer_piece, model_state)
    command_list = get_model_commands(layer_piece_t, command_ctx)
    idx_command_by_d = {
        cmd.d: (idx, cmd) for idx, cmd
        in enumerate(command_list)
        }
    current_command_d = pyobj_creg.invite(current_item.command_d)
    if current_command_d == prev_command_d:
        new_command_d = None
    else:
        new_command_d = current_command_d
    new_adapter = _amend_adapter(data_to_ref, root_piece_t, layer_piece_t, adapter, new_command_d)
    new_view = htypes.tree.view(
        adapter=mosaic.put(new_adapter),
        )
    set_custom_layout(lcs, root_piece_t, new_view)
    feed = feed_factory(piece)
    try:
        idx, prev_command = idx_command_by_d[prev_command_d]
    except KeyError:
        pass
    else:
        prev_item = _make_command_item(data_to_ref, prev_command, is_opener=False)
        await feed.send(ListDiff.Replace(idx, prev_item))
    try:
        idx, current_command = idx_command_by_d[current_command_d]
    except KeyError:
        pass
    else:
        assert idx == current_idx
        item = _make_command_item(data_to_ref, current_command, is_opener=new_command_d is not None)
        await feed.send(ListDiff.Replace(current_idx, item))
