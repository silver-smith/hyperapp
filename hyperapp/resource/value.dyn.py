from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type
from hyperapp.common.module import Module

from . import htypes


class ValueResourceType:

    def __init__(self, mosaic, types):
        self._mosaic = mosaic
        self._types = types

    def parse(self, data):
        value = data['value']
        t = deduce_complex_value_type(self._mosaic, self._types, value)
        value_ref = self._mosaic.put(value, t)
        return htypes.value.value(value_ref)

    def resolve(self, definition, resolve_name):
        return definition


def python_object(piece, web):
    return web.summon(piece.value_ref)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_reg['value'] = ValueResourceType(services.mosaic, services.types)
        services.python_object_creg.register_actor(htypes.value.value, python_object, services.web)
