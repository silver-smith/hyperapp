from functools import partial

from hyperapp.common.module import Module

from . import htypes


def python_object(piece, mosaic, python_object_creg):
    identity = python_object_creg.invite(piece.identity)
    peer_ref = mosaic.put(identity.peer.piece)
    return htypes.rpc_callback.rpc_callback(
        peer_ref=peer_ref,
        servant_fn_ref=piece.function,
        item_attr_list=piece.item_attributes,
        )


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.python_object_creg.register_actor(
            htypes.resource_rpc_callback.rpc_callback, python_object, services.mosaic, services.python_object_creg)
