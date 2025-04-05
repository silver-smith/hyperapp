from . import htypes
from .code.mark import mark


@mark.model(key='name')
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


@mark.selector.get
def layer_get(value):
    piece = htypes.config_layer_list.model()
    return (piece, value.name)


@mark.selector.pick
def layer_pick(piece, current_item):
    return htypes.config_layer_list.layer(
        name=current_item.name,
        )
