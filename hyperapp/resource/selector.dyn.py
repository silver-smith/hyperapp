from hyperapp.common.module import Module

from . import htypes


def python_object(piece):
    return piece


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_reg['selector'] = services.resource_type_factory(htypes.selector.selector)
        services.python_object_creg.register_actor(htypes.selector.selector, python_object)
