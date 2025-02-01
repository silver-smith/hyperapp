from operator import itemgetter

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
                    yield str(key), item
        else:
            yield ('', config)

    config = system.get_config_template(piece.service_name)
    return [
        htypes.config_item_list.item(
            key=key_str,
            value=str(value),
            )
        for key_str, value
        in sorted(enum_items(config), key=itemgetter(0))
        ]


@mark.command
def open_config_item_list(piece, current_item):
    return htypes.config_item_list.model(current_item.service_name)
