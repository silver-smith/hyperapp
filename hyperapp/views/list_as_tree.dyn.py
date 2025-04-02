import logging

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.list_diff import ListDiff
from .code.command import command_text
from .code.fn_list_adapter import FnListAdapter
from .code.list_as_tree_adapter import ListAsTreeAdapter
from .code.model_command import model_command_ctx

log = logging.getLogger(__name__)


@mark.view_factory.ui_t
def list_as_tree_ui_type_layout(piece, system_fn_ref):
    adapter = htypes.list_as_tree_adapter.adapter(
        root_item_t=piece.item_t,
        root_function=system_fn_ref,
        root_open_children_command=None,
        layers=(),
        )
    return htypes.tree.view(
        adapter=mosaic.put(adapter),
        )


@mark.ui_command(htypes.list.view)
def switch_list_to_tree(piece, view, hook, ctx, view_reg):
    list_adapter = view.adapter
    if not isinstance(list_adapter, FnListAdapter):
        log.info("Switch list to tree: Not an FnListAdapter: %r", list_adapter)
        return
    item_t_res = pyobj_creg.actor_to_piece(list_adapter.item_t)
    adapter = htypes.list_as_tree_adapter.adapter(
        root_item_t=mosaic.put(item_t_res),
        root_function=mosaic.put(list_adapter.function.piece),
        root_open_children_command=None,
        layers=(),
        )
    new_view_piece = htypes.tree.view(
        adapter=mosaic.put(adapter),
        )
    model_ctx = ctx.clone_with(model=piece)
    new_view = view_reg.animate(new_view_piece, model_ctx)
    hook.replace_view(new_view)


@mark.model
def list_as_tree_layers(piece):
    pass


@mark.ui_command
def open_layers(view, current_item, model):
    adapter = view.adapter
    if not isinstance(adapter, ListAsTreeAdapter):
        log.info("Not a ListAsTreeAdapter: %r", adapter)
        return
    adapter_piece = web.summon(view.piece.adapter)
    root_piece_t = deduce_t(model)
    return htypes.list_as_tree.layer_list(
        root_piece_t=pyobj_creg.actor_to_ref(root_piece_t),
        root_open_children_command=adapter_piece.root_open_children_command,
        layers=adapter_piece.layers,
        )


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


def _make_command_item(format, command, is_opener):
    return htypes.list_as_tree.opener_command_item(
        command=mosaic.put(command.piece),
        name=command_text(format, command),
        is_opener=is_opener,
        )


def _get_current_command(command_creg, root_piece_t, layer_piece_t, adapter):
    if root_piece_t == layer_piece_t:
        return command_creg.invite_opt(adapter.root_open_children_command)
    for layer in adapter.layers:
        t = pyobj_creg.invite(layer.piece_t)
        if t == layer_piece_t:
            return command_creg.invite_opt(layer.open_children_command)
    # Layer is not yet included into adapter piece.
    return None


def _amend_adapter(root_piece_t, layer_piece_t, adapter, new_command):
    new_command_ref = mosaic.put_opt(new_command.piece)
    layers = list(adapter.layers)
    if root_piece_t == layer_piece_t:
        root_open_children_command = new_command_ref
    else:
        root_open_children_command = adapter.root_open_children_command
        for idx, layer in enumerate(adapter.layers):
            t = pyobj_creg.invite(layer.piece_t)
            if t == layer_piece_t:
                new_layer = htypes.list_as_tree_adapter.layer(
                    piece_t=layer.piece_t,
                    open_children_command=new_command_ref,
                    )
                layers[idx] = new_layer
                break
        else:
            piece_t_res = pyobj_creg.actor_to_piece(layer_piece_t)
            new_layer = htypes.list_as_tree_adapter.layer(
                piece_t=mosaic.put(piece_t_res),
                open_children_command=new_command_ref,
                )
            layers.append(new_layer)
    return htypes.list_as_tree_adapter.adapter(
        root_item_t=adapter.root_item_t,
        root_function=adapter.root_function,
        root_open_children_command=root_open_children_command,
        layers=tuple(layers),
        )


def _type_key(model_t):
    return htypes.ui.model_layout_k(
        model_t=pyobj_creg.actor_to_ref(model_t),
        )


@mark.model
def opener_command_list(piece, ctx, format, command_creg, get_model_commands, model_layout_reg):
    root_piece, root_piece_t = web.summon_with_t(piece.root_piece)
    layer_piece, layer_piece_t = web.summon_with_t(piece.layer_piece)
    model_state = web.summon(piece.model_state)
    view = model_layout_reg.get(_type_key(root_piece_t))
    current_command = None
    if isinstance(view, htypes.tree.view):
        adapter = web.summon(view.adapter)
        if isinstance(adapter, htypes.list_as_tree_adapter.adapter):
            current_command = _get_current_command(command_creg, root_piece_t, layer_piece_t, adapter)
    command_ctx = model_command_ctx(ctx, layer_piece, model_state)
    command_list = get_model_commands(layer_piece_t, command_ctx)
    return [
        _make_command_item(format, command, is_opener=current_command is not None and command.d == current_command.d)
        for command in command_list
        ]


@mark.command
async def toggle_open_command(
        piece, current_idx, current_item, ctx,
        format, feed_factory, command_creg, get_model_commands, model_layout_reg):
    root_piece, root_piece_t = web.summon_with_t(piece.root_piece)
    layer_piece, layer_piece_t = web.summon_with_t(piece.layer_piece)
    model_state = web.summon(piece.model_state)
    root_piece_k = _type_key(root_piece_t)
    view = model_layout_reg.get(root_piece_k)
    if not isinstance(view, htypes.tree.view):
        log.info("View for %s is not a tree: %s", root_piece_t, view)
        return
    adapter = web.summon(view.adapter)
    if not isinstance(adapter, htypes.list_as_tree_adapter.adapter):
        log.info("Adapter for %s is not a list-to-tree: %s", model_t, adapter)
        return
    prev_command = _get_current_command(command_creg, root_piece_t, layer_piece_t, adapter)
    command_ctx = model_command_ctx(ctx, layer_piece, model_state)
    command_list = get_model_commands(layer_piece_t, command_ctx)
    idx_command_by_d = {
        cmd.d: (idx, cmd) for idx, cmd
        in enumerate(command_list)
        }
    current_command = command_creg.invite(current_item.command)
    if current_command and prev_command and current_command.d == prev_command.d:
        new_command = None
    else:
        new_command = current_command
    new_adapter = _amend_adapter(root_piece_t, layer_piece_t, adapter, new_command)
    new_view = htypes.tree.view(
        adapter=mosaic.put(new_adapter),
        )
    model_layout_reg[root_piece_k] = new_view
    feed = feed_factory(piece)

    if prev_command:
        try:
            idx, prev_command = idx_command_by_d[prev_command.d]
        except KeyError:
            pass
        else:
            prev_item = _make_command_item(format, prev_command, is_opener=False)
            await feed.send(ListDiff.Replace(idx, prev_item))
    if current_command:
        try:
            idx, current_command = idx_command_by_d[current_command.d]
        except KeyError:
            pass
        else:
            assert idx == current_idx
            item = _make_command_item(format, current_command, is_opener=new_command is not None)
            await feed.send(ListDiff.Replace(current_idx, item))
