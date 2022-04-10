from functools import partial

from hyperapp.common.module import Module

from .cached_code_registry import CachedCodeRegistry


def resource_type_producer(resource_type_factory, resource_type_reg, resource_t):
    try:
        return resource_type_reg[resource_t]
    except KeyError:
        return resource_type_factory(resource_t)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_reg = {}  # resource_t -> ResourceType instance
        services.python_object_creg = CachedCodeRegistry('python_object', services.web, services.types)
        services.resource_type_producer = partial(resource_type_producer, services.resource_type_factory, services.resource_type_reg)
