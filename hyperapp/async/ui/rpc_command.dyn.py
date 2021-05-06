from hyperapp.common.htypes import (
    optional_mt,
    field_mt,
    record_mt,
    request_mt,
    interface_mt,
    name_wrapped_mt,
    ref_t,
    )
from hyperapp.common.module import Module

from . import htypes
from .resource_key import module_resource_key


def element_command_interface_ref(mosaic, types, key_type_ref, method_name):
    item_key_field = field_mt('item_key', key_type_ref)
    opt_ref_ref = optional_mt(types.reverse_resolve(ref_t))
    piece_field = field_mt('piece_ref', mosaic.put(opt_ref_ref))
    method_ref = mosaic.put(request_mt(method_name, [item_key_field], [piece_field]))
    interface_ref = mosaic.put(interface_mt(None, [method_ref]))
    named_interface_ref = mosaic.put(name_wrapped_mt(f'rpc_element_command_{method_name}_interface', interface_ref))
    return named_interface_ref


class RpcElementCommand:

    @classmethod
    async def from_piece(cls, piece, command_id, mosaic, types, web, rpc_endpoint, async_rpc_proxy, identity):
        interface_ref = element_command_interface_ref(mosaic, types, piece.key_type_ref, piece.method_name)
        service = htypes.rpc.endpoint(
            peer_ref=piece.peer_ref,
            iface_ref=interface_ref,
            object_id=piece.object_id,
            )
        proxy = async_rpc_proxy(identity, rpc_endpoint, service)
        return cls(web, command_id, piece.key_type_ref, piece.method_name, piece.peer_ref, piece.object_id, proxy)

    def __init__(self, web, id, key_type_ref, method_name, peer_ref, object_id, proxy):
        self._web = web
        self.id = id
        self._key_type_ref = key_type_ref
        self._method_name = method_name
        self._peer_ref = peer_ref
        self._object_id = object_id
        self._proxy = proxy

    def is_enabled(self):
        return True

    @property
    def kind(self):
        return 'element'

    @property
    def resource_key(self):
        cls = self.__class__
        class_name = cls.__name__
        module_name = cls.__module__
        return module_resource_key(module_name, [class_name, 'command', self.id])

    @property
    def piece(self):
        return htypes.rpc_command.rpc_element_command(
            key_type_ref=self._key_type_ref,
            method_name=self._method_name,
            peer_ref=self._peer_ref,
            object_id=self._object_id,
            )

    async def run(self, item_key):
        method = getattr(self._proxy, self._method_name)
        response = await method(item_key)
        return await self._web.summon_opt(response.piece_ref)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

    async def async_init(self, services):
        services.command_registry.register_actor(
            htypes.rpc_command.rpc_element_command, RpcElementCommand.from_piece,
            services.mosaic, services.types, services.async_web,
            services.client_rpc_endpoint, services.async_rpc_proxy, services.client_identity)
