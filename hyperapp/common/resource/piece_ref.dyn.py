from functools import partial

from hyperapp.common.module import Module

from . import htypes


def factory(data, resolve_name):
    value_ref = resolve_name(data['value'])
    return htypes.piece_ref.piece_ref(value_ref)


def python_object(piece):
    return piece.value_ref


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry['piece_ref'] = factory
        services.python_object_creg.register_actor(htypes.piece_ref.piece_ref, python_object)
