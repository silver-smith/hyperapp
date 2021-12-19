from hyperapp.common.module import Module

from . import htypes


def from_dict(data, name_to_resource):
    fn_object_ref = name_to_resource[data['function']]
    return htypes.call.call(fn_object_ref)


def python_object(piece, python_object_creg):
    fn = python_object_creg.invite(piece.fn_object_ref)
    return fn()


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry['call'] = from_dict
        services.python_object_creg.register_actor(htypes.call.call, python_object, services.python_object_creg)
