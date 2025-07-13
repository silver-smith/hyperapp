from collections import defaultdict

from hyperapp.boot.htypes import Type
from hyperapp.boot.htypes.deduce_value_type import DeduceTypeError

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.data_browser import data_browser


def _enum_items(config):
    if type(config) in {list, set}:
        for item in config:
            yield ('', item)
    elif type(config) is dict:
        for key, value in config.items():
            for _, item in _enum_items(value):
                yield key, item
    else:
        yield ('', config)


@mark.model(key='key')
def config_item_list(piece, system, format):

    key_to_item_layer = defaultdict(list)
    for layer_name, layer in system.name_to_layer.items():
        try:
            config = layer.config[piece.service_name]
        except KeyError:
            continue
        for key, value in _enum_items(config):
            key_to_item_layer[key].append((value, layer_name))

    def item_layers(key, value):
        result = []
        for v, layer_name in key_to_item_layer.get(key, []):
            if v is value:
                result.append(layer_name)
        return result

    config_template = system.get_config_template(piece.service_name)

    item_list = []
    for key, value in sorted(_enum_items(config_template), key=lambda rec: str(rec[0])):
        if isinstance(key, Type):
            key_data = pyobj_creg.actor_to_piece(key)
        else:
            key_data = key
        try:
            deduce_t(value)
            value_data = value
        except DeduceTypeError:
            value_data = None  # TODO: do these cases exists?
        layers = item_layers(key, value)
        item = htypes.config_item_list.item(
            key=mosaic.put(key_data),
            key_str=format(key),
            value=mosaic.put_opt(value),
            value_str=str(value),
            layers=tuple(layers),
            layers_str=", ".join(layers),
            )
        item_list.append(item)
    return item_list


@mark.model(key='key')
def config_item_layer_list(piece, system, format):
    config_template = system.get_layer_config_templates(piece.layer).get(piece.service_name)
    item_list = []
    for key, value in sorted(_enum_items(config_template), key=lambda rec: str(rec[0])):
        if isinstance(key, Type):
            key_data = pyobj_creg.actor_to_piece(key)
        else:
            key_data = key
        try:
            deduce_t(value)
            value_data = value
        except DeduceTypeError:
            value_data = None  # TODO: do these cases exists?
        item = htypes.config_item_list.layer_item(
            key=mosaic.put(key_data),
            key_str=format(key),
            value=mosaic.put_opt(value),
            value_str=str(value),
            )
        item_list.append(item)
    return item_list


@mark.command(preserve_remote=True)
def open_config_item_list(piece, current_item):
    if piece.layer:
        return htypes.config_item_list.layer_model(
            layer=piece.layer,
            service_name=current_item.service_name,
            )
    else:
        return htypes.config_item_list.model(
            service_name=current_item.service_name,
            )


@mark.command
def open_config_key(piece, current_item):
    key = web.summon(current_item.key)
    return data_browser(key)


@mark.command
def open_config_value(piece, current_item):
    value = web.summon(current_item.value)
    return data_browser(value)


def _move_item(system, source_layer_name, target_layer_name, service_name, key):
    source_layer = system.name_to_layer[source_layer_name]
    target_layer = system.name_to_layer[target_layer_name]
    key_piece = web.summon(key)
    service_config = system.get_config_template(service_name)
    value_template = service_config[key_piece]
    target_layer.set(service_name, key_piece, value_template)
    source_layer.remove(service_name, key_piece)


@mark.crud.get_layer(commit_action='move')
def config_item_get_layer(piece, layers):
    if not layers:
        return None
    return htypes.config_layer_list.layer(
        name=layers[0],
        )


@mark.crud.move
def config_item_move_to_another_layer(piece, key, layers, value, system):
    source_layer_name = layers[0]
    target_layer_name = value.name
    if target_layer_name == source_layer_name:
        return
    _move_item(system, source_layer_name, target_layer_name, piece.service_name, key)
    return (piece, key)



@mark.crud.get_layer(commit_action='move')
def config_layer_item_get_layer(piece):
    return htypes.config_layer_list.layer(
        name=piece.layer,
        )


@mark.crud.move
def config_layer_item_move_to_another_layer(piece, key, value, system):
    source_layer_name = piece.layer
    target_layer_name = value.name
    if target_layer_name == source_layer_name:
        return
    _move_item(system, source_layer_name, target_layer_name, piece.service_name, key)
    target_piece = htypes.config_item_list.layer_model(
        layer=target_layer_name,
        service_name=piece.service_name,
        )
    return (target_piece, key)


def _remove_item(system, layer_name, service_name, key):
    layer = system.name_to_layer[layer_name]
    key = web.summon(key)
    layer.remove(service_name, key)


@mark.command.remove
def remove(piece, current_item, system):
    layer_name = current_item.layers[0]  # Will remove from first layer.
    _remove_item(system, layer_name, piece.service_name, current_item.key)
    return True


@mark.command.remove
def layer_remove(piece, current_item, system):
    layer_name = piece.layer
    _remove_item(system, layer_name, piece.service_name, current_item.key)
    return True


@mark.actor.formatter_creg
def format_model(piece):
    return f"Config: {piece.service_name}"


@mark.actor.formatter_creg
def format_layer_model(piece):
    return f"Config: {piece.layer}/{piece.service_name}"
