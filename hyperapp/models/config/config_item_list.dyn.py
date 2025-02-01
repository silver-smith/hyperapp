from . import htypes
from .code.mark import mark


@mark.model
def config_item_list(piece, system):
    return [
        htypes.config_item_list.item(
            key=str(key),
            value=str(value),
            )
        for key, value
        in sorted(system.get_config_template(piece.service_name).items())
        ]


@mark.command
def open_config_item_list(piece, current_item):
    return htypes.config_item_list.model(current_item.service_name)
