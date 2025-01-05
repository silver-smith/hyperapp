import logging

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.directory import d_to_name

log = logging.getLogger(__name__)



@mark.model
def lcs_layers_model(piece, lcs):
    return [
        htypes.lcs_layer.item(
            name=d_to_name(layer_d),
            d=mosaic.put(layer_d),
            )
        for layer_d in sorted(lcs.layers())
        ]


@mark.command
def lcs_open_layers(piece):
    return htypes.lcs_layer.model()


@mark.selector.get
def layer_get(value):
    return htypes.lcs_layer.model()


@mark.selector.put
def layer_put(piece, current_item):
    return htypes.lcs_layer.layer(
        d=current_item.d,
        )


@mark.actor.model_layout_creg
def layer_selector_layout(piece, lcs, ctx, visualizer):
    return visualizer(lcs, ctx, htypes.lcs_layer.model())


@mark.command
def select_layer(piece, current_item, lcs):
    source_layer_d = web.summon(piece.source_layer_d)
    dir = [web.summon(d) for d in piece.dir]
    target_layer_d = web.summon(current_item.d)
    if target_layer_d == source_layer_d:
        return
    lcs.move(dir, source_layer_d, target_layer_d)
    return htypes.lcs_view.view(filter=())
