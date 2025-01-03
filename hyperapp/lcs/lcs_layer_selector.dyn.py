import logging

from . import htypes
from .services import (
    web,
    )
from .code.mark import mark

log = logging.getLogger(__name__)


@mark.selector.get
def layer_get(value):
    return htypes.lcs_view.layers_view()


@mark.selector.put
def layer_put(piece, current_item):
    return htypes.lcs_view.layer(
        d=current_item.d,
        )


@mark.actor.model_layout_creg
def layer_selector_layout(piece, lcs, ctx, visualizer):
    return visualizer(lcs, ctx, htypes.lcs_view.layers_view())


@mark.command
def select_layer(piece, current_item, lcs):
    source_layer_d = web.summon(piece.source_layer_d)
    dir = [web.summon(d) for d in piece.dir]
    target_layer_d = web.summon(current_item.d)
    if target_layer_d == source_layer_d:
        return
    lcs.move(dir, source_layer_d, target_layer_d)
    return htypes.lcs_view.view(filter=())
