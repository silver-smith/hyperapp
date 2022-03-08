from functools import partial

from hyperapp.common.module import Module

from . import htypes


def python_object(piece):
    return piece.value


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_reg['piece_ref'] = services.resource_type_factory('piece_ref', htypes.piece_ref.piece_ref)
        services.python_object_creg.register_actor(htypes.piece_ref.piece_ref, python_object)
