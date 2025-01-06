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


@mark.selector.pick
def layer_put(piece, current_item):
    return htypes.lcs_layer.layer(
        layer_d=current_item.d,
        )
