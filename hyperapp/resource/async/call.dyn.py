from hyperapp.common.module import Module

from . import htypes


async def python_object(piece, python_object_acreg):
    fn = await python_object_acreg.invite(piece.function)
    return fn()


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.python_object_acreg.register_actor(htypes.call.call, python_object, services.python_object_acreg)
