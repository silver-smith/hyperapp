from . import htypes
from .services import (
    builtin_services,
    )
from .code.import_resource import ImportResource


def enum_builtin_resources(module_name):
    for service_name in builtin_services:
        piece = htypes.builtin.builtin_service(service_name)
        yield ImportResource(module_name, ['services', service_name], piece)
