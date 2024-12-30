from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.list_diff import ListDiff
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


@mark.model
def lcs_layers_view(piece, lcs):
    return [
        htypes.lcs_view.layer_item(
            name=d_to_name(layer_d),
            d=mosaic.put(layer_d),
            )
        for layer_d in sorted(lcs.layers())
        ]


@mark.command
def lcs_open_layers(piece):
    return htypes.lcs_view.layers_view()


@mark.command
async def lcs_remove(piece, current_idx, current_item, lcs, feed_factory):
    feed = feed_factory(piece)
    dir = {web.summon(d) for d in current_item.dir}
    lcs.remove(dir)
    await feed.send(ListDiff.Remove(current_idx))


@mark.command
def lcs_move_to_another_layer(piece, current_item):
    return htypes.lcs_view.layer_selector(
        source_layer_d=current_item.layer_d,
        dir=current_item.dir,
        )


@mark.command
def lcs_open_piece(piece, current_item):
    item_piece = web.summon(current_item.piece)
    return data_browser(item_piece)

    
@mark.global_command
def open_lcs_view():
    return htypes.lcs_view.view(filter=())
