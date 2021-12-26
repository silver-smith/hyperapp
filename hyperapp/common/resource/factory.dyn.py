from functools import partial

from hyperapp.common.module import Module

from . import htypes


def factory(data, resolve_name):
    object_ref = resolve_name(data['object'])
    attr_name = data['attr_name']
    params = [
        htypes.factory.param(name, resolve_name(resource_name))
        for name, resource_name
        in data.get('params', {}).items()
        ]
    return htypes.factory.factory(object_ref, attr_name, params)


def python_object(piece, python_object_creg):
    object = python_object_creg.invite(piece.object_ref)
    kw = {
        param.name: python_object_creg.invite(param.value_ref)
        for param in piece.params
        }
    fn = getattr(object, piece.attr_name)
    if kw:
        return partial(fn, **kw)
    else:
        return fn


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry['factory'] = factory
        services.python_object_creg.register_actor(htypes.factory.factory, python_object, services.python_object_creg)
