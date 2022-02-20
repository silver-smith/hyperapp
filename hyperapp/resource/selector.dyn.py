from hyperapp.common.module import Module

from . import htypes


def python_object(piece, mosaic, python_object_creg):
    list_service = python_object_creg.invite(piece.list_service)
    callback = python_object_creg.invite(piece.callback)
    return htypes.selector.selector(
        list_service_ref=mosaic.put(list_service),
        callback_ref=mosaic.put(callback),
        )


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_reg['selector'] = services.resource_type_factory(htypes.resource_selector.selector)
        services.python_object_creg.register_actor(htypes.resource_selector.selector, python_object, services.mosaic, services.python_object_creg)
