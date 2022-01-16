from functools import partial

from hyperapp.common.module import Module

from . import htypes


async def python_object(piece, python_object_acreg):
    fn = await python_object_acreg.invite(piece.fn_ref)
    kw = {
        param.name: await python_object_acreg.invite(param.value_ref)
        for param in piece.params
        }
    return partial(fn, **kw)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.python_object_acreg.register_actor(htypes.partial.partial, python_object, services.python_object_acreg)
