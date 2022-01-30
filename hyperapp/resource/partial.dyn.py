from functools import partial

from hyperapp.common.module import Module

from . import htypes


def python_object(piece, python_object_creg):
    fn = python_object_creg.invite(piece.function)
    kw = {
        param.name: python_object_creg.invite(param.value)
        for param in piece.params
        }
    return partial(fn, **kw)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_reg['partial'] = services.resource_type_factory(htypes.partial.partial)
        services.python_object_creg.register_actor(htypes.partial.partial, python_object, services.python_object_creg)
