from functools import partial

from hyperapp.common.module import Module

from . import htypes


def python_object(piece):
    return piece.value


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.python_object_creg.register_actor(htypes.piece_ref.piece_ref, python_object)
