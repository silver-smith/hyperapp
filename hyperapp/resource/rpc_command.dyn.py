from functools import partial

from hyperapp.common.module import Module

from . import htypes


def factory(mosaic, python_object_creg, data, resolve_name):
    identity_ref = resolve_name(data['identity'])
    identity = python_object_creg.invite(identity_ref)
    peer_ref = mosaic.put(identity.peer.piece)
    servant_fn_ref = resolve_name(data['servant'])
    state_attr_list = data['state_attributes']
    name = data['name']
    return htypes.rpc_command.rpc_command(
        peer_ref=peer_ref,
        servant_fn_ref=servant_fn_ref,
        state_attr_list=state_attr_list,
        name=name,
        )


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry['rpc_command'] = partial(
            factory, services.mosaic, services.python_object_creg)
