from hyperapp.common.module import Module

from . import htypes


def factory(data, resolve_name):
    fn_object_ref = resolve_name(data['function'])
    return htypes.call.call(fn_object_ref)


def python_object(piece, python_object_creg):
    fn = python_object_creg.invite(piece.fn_object_ref)
    return fn()


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry['call'] = factory
        services.python_object_creg.register_actor(htypes.call.call, python_object, services.python_object_creg)
