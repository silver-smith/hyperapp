from functools import partial

from hyperapp.common.module import Module

from . import htypes


def from_dict(data, name_to_piece_ref):
    object_ref = name_to_piece_ref[data['object']]
    attr_name = data['attr_name']
    params = [
        htypes.factory.param(name, name_to_piece_ref[resource_name])
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

        services.resource_type_registry['factory'] = from_dict
        services.python_object_creg.register_actor(htypes.factory.factory, python_object, services.python_object_creg)
