from . import htypes
from .code.mark import mark


@mark.model
def config_service_list(piece, system):
    return [
        htypes.config_service_list.item(
            service_name=service_name,
            item_count=len(system.get_config_template(service_name)),
            )
        for service_name in sorted(system.service_names)
        ]


@mark.global_command
def open_config_service_list():
    return htypes.config_service_list.model()
