from functools import partial

from hyperapp.common.module import Module

from . import htypes


def factory(data, resolve_name):
    fn_ref = resolve_name(data['function'])
    params = [
        htypes.partial.param(name, resolve_name(resource_name))
        for name, resource_name
        in data['params'].items()
        ]
    return htypes.partial.partial(fn_ref, params)


def python_object(piece, python_object_creg):
    fn = python_object_creg.invite(piece.fn_ref)
    kw = {
        param.name: python_object_creg.invite(param.value_ref)
        for param in piece.params
        }
    return partial(fn, **kw)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry['partial'] = factory
        services.python_object_creg.register_actor(htypes.partial.partial, python_object, services.python_object_creg)
