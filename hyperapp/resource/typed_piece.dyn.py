from functools import partial

from hyperapp.common.module import Module

from . import htypes


def python_object(piece, python_object_creg):
    t = python_object_creg.invite(piece.piece_t)
    object_piece = t()  # Only types with no fields are supported.
    return python_object_creg.animate(object_piece)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_reg['typed_piece'] = services.resource_type_factory('typed_piece', htypes.typed_piece.typed_piece)
        services.python_object_creg.register_actor(
            htypes.typed_piece.typed_piece, python_object, services.python_object_creg)
