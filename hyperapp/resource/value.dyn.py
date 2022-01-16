from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type
from hyperapp.common.module import Module

from . import htypes


def factory(mosaic, types, data, resolve_name):
    value = data['value']
    t = deduce_complex_value_type(mosaic, types, value)
    value_ref = mosaic.put(value, t)
    return htypes.value.value(value_ref)


def python_object(piece, web):
    return web.summon(piece.value_ref)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry['value'] = partial(factory, services.mosaic, services.types)
        services.python_object_creg.register_actor(htypes.value.value, python_object, services.web)
