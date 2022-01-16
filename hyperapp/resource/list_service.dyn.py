from functools import partial

from hyperapp.common.module import Module

from . import htypes


def factory(mosaic, python_object_creg, data, resolve_name):
    identity_ref = resolve_name(data['identity'])
    identity = python_object_creg.invite(identity_ref)
    peer_ref = mosaic.put(identity.peer.piece)
    servant_fn_ref = resolve_name(data['servant'])
    dir = [
        mosaic.put(d)
        for d in data['dir']
        ]
    command_ref_list = [
        resolve_name(command_name)
        for command_name
        in data.get('commands', [])
        ]
    key_attribute = data['key_attribute']
    return htypes.service.list_service(
        peer_ref=peer_ref,
        servant_fn_ref=servant_fn_ref,
        dir_list=[dir],
        command_ref_list=command_ref_list,
        key_attribute=key_attribute,
        )


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry['list_service'] = partial(
            factory, services.mosaic, services.python_object_creg)
