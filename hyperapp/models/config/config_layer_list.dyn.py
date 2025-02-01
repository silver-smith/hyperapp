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
def config_layer_list(piece, system):
    return [
        htypes.config_layer_list.item(
            name=name,
            service_count=len(layer.config),
            )
        for name, layer in system.name_to_layer.items()
        ]


@mark.global_command
def open_config_layer_list():
    return htypes.config_layer_list.model()
