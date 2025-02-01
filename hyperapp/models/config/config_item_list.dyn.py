from collections import defaultdict

from . import htypes
from .code.mark import mark


@mark.model
def config_item_list(piece, system):

    def enum_items(config):
        if type(config) in {list, set}:
            for item in config:
                yield ('', item)
        elif type(config) is dict:
            for key, value in config.items():
                for _, item in enum_items(value):
                    yield key, item
        else:
            yield ('', config)

    key_to_item_layer = defaultdict(list)
    for layer_name, layer in system.name_to_layer.items():
        try:
            config = layer.config[piece.service_name]
        except KeyError:
            continue
        for key, value in enum_items(config):
            key_to_item_layer[key].append((value, layer_name))

    def item_layers(key, value):
        result = []
        for v, layer_name in key_to_item_layer.get(key, []):
            if v is value:
                result.append(layer_name)
        return result

    config = system.get_config_template(piece.service_name)
    return [
        htypes.config_item_list.item(
            key=str(key),
            value=str(value),
            layers=", ".join(item_layers(key, value)),
            )
        for key, value
        in sorted(enum_items(config), key=lambda rec: str(rec[0]))
        ]


@mark.command
def open_config_item_list(piece, current_item):
    return htypes.config_item_list.model(current_item.service_name)
