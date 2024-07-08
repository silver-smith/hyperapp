from . import htypes
from .services import (
    builtin_services,
    mark,
    pyobj_creg,
    )
from .code.import_resource import ImportResource


def enum_builtin_resources():
    for service_name in builtin_services:
        piece = htypes.builtin.builtin_service(service_name)
        yield ImportResource(['services', service_name], piece)
    mark_service_piece = pyobj_creg.actor_to_piece(mark)
    yield ImportResource(['services', 'mark'], mark_service_piece)
