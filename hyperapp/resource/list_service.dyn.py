from functools import partial

from hyperapp.common.module import Module

from . import htypes


def python_object(piece, mosaic, python_object_creg):
    identity = python_object_creg.invite(piece.identity)
    peer_ref = mosaic.put(identity.peer.piece)
    dir = python_object_creg.invite(piece.dir)
    return htypes.service.list_service(
        peer_ref=peer_ref,
        servant_fn_ref=piece.function,
        dir_list=[[mosaic.put(dir)]],
        command_ref_list=[
            mosaic.put(python_object_creg.invite(command_ref))
            for command_ref
            in piece.commands
            ],
        key_attribute=piece.key_attribute,
        )


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_reg['list_service'] = services.resource_type_factory('list_service', htypes.resource_service.list_service)
        services.python_object_creg.register_actor(
            htypes.resource_service.list_service, python_object, services.mosaic, services.python_object_creg)
