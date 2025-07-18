from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.list_diff import IndexListDiff
from .code.directory import d_to_name
from .code.data_browser import data_browser


def dir_to_str(d):
    if isinstance(d, htypes.builtin.list_mt):
        base = dir_to_str(web.summon(d.element))
        return f'{base} list'
    if isinstance(d, htypes.builtin.record_mt):
        return f'{d.module_name}.{d.name}'
    else:
        return str(d)


@mark.model
def lcs_view(piece, lcs):
    filter = {
        web.summon(d_ref)
        for d_ref in piece.filter
        }
    return [
        htypes.lcs_view.item(
            layer_d=mosaic.put(layer_d),
            layer=d_to_name(layer_d),
            dir=tuple(mosaic.put(d) for d in dir_set),
            piece=mosaic.put(piece),
            dir_str=", ".join(sorted(dir_to_str(d) for d in dir_set)),
            piece_str=str(piece),
            )
        for layer_d, dir_set, piece in sorted(lcs)
        if not filter or filter & dir_set 
        ]


@mark.command
def lcs_remove(piece, current_idx, current_item, lcs, feed_factory):
    feed = feed_factory(piece)
    dir = {web.summon(d) for d in current_item.dir}
    lcs.remove(dir)
    feed.send(IndexListDiff.Remove(current_idx))


@mark.crud.get_layer(commit_action='move')
def lcs_get_layer(piece, layer_d):
    return htypes.lcs_layer.layer(
        layer_d=layer_d,
        )


@mark.crud.move
def lcs_move_to_another_layer(piece, dir, layer_d, value, lcs):
    source_layer_d = web.summon(layer_d)
    dir_actor = [web.summon(d) for d in dir]
    target_layer_d = web.summon(value.layer_d)
    if target_layer_d == source_layer_d:
        return
    lcs.move(dir_actor, source_layer_d, target_layer_d)
    return htypes.lcs_view.view(filter=())


@mark.command
def lcs_open_piece(piece, current_item):
    item_piece = web.summon(current_item.piece)
    return data_browser(item_piece)

    
@mark.global_command
def open_lcs_view():
    return htypes.lcs_view.view(filter=())
