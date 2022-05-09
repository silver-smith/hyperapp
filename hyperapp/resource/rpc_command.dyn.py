from functools import partial

from hyperapp.common.module import Module

from . import htypes


def python_object(piece, mosaic, python_object_creg):
    identity = python_object_creg.invite(piece.identity)
    peer_ref = mosaic.put(identity.peer.piece)
    return htypes.rpc_command.rpc_command(
        peer_ref=peer_ref,
        servant_fn_ref=piece.function,
        state_attr_list=piece.params,
        name=piece.name,
        )


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.python_object_creg.register_actor(
            htypes.resource_rpc_command.rpc_command, python_object, services.mosaic, services.python_object_creg)
