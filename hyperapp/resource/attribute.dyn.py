from hyperapp.common.module import Module

from . import htypes


def factory(data, resolve_name):
    object_ref = resolve_name(data['object'])
    attr_name = data['attr_name']
    return htypes.attribute.attribute(object_ref, attr_name)


def python_object(piece, python_object_creg):
    object = python_object_creg.invite(piece.object_ref)
    return getattr(object, piece.attr_name)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry['attribute'] = factory
        services.python_object_creg.register_actor(htypes.attribute.attribute, python_object, services.python_object_creg)
