from hyperapp.common.htypes.legacy_service import legacy_service_t
from hyperapp.common.module import Module

from . import htypes
from .legacy_service import builtin_service_python_object


async def module_service_python_object(piece, python_object_acreg, services):
    _ = await python_object_acreg.invite(piece.module_ref)  # Ensure it is loaded.
    return getattr(services, piece.name)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.python_object_acreg.register_actor(legacy_service_t, builtin_service_python_object, services)
        services.python_object_acreg.register_actor(htypes.legacy_service.module_service, module_service_python_object, services.python_object_acreg, services)
