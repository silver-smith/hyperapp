from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.module import Module

from .code_registry import CodeRegistry, CodeRegistryKeyError
from .async_rpc_proxy import AsyncRpcProxy


async def adapter_factory(
        python_object_creg,
        impl_registry,
        service_provider_reg,
        adapter_registry,
        async_rpc_call_factory,
        async_rpc_endpoint_holder,
        identity,
        piece,
        ):
    try:
        provider, servant_ref, spec = service_provider_reg[piece]
    except KeyError:
        piece_t = deduce_value_type(piece)
        ctr_fn_piece, spec = impl_registry[piece_t]
        if ctr_fn_piece is not None:
            ctr_fn = python_object_creg.animate(ctr_fn_piece)
            object = ctr_fn(piece)
        else:
            object = piece
    else:
        async_rpc_endpoint = async_rpc_endpoint_holder[0]
        object = AsyncRpcProxy(
            async_rpc_call_factory=async_rpc_call_factory,
            async_rpc_endpoint=async_rpc_endpoint,
            identity=identity,
            peer=provider,
            servant_ref=servant_ref,
            )
    return await adapter_registry.animate(spec, piece, object)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._async_rpc_endpoint_holder = []
        services.adapter_registry = CodeRegistry('adapter', services.async_web, services.types)
        services.adapter_factory = partial(
            adapter_factory,
            services.python_object_creg,
            services.impl_registry,
            services.service_provider_reg,
            services.adapter_registry,
            services.async_rpc_call_factory,
            self._async_rpc_endpoint_holder,
            services.client_identity,
            )

    async def async_init(self, services):
        self._async_rpc_endpoint_holder.append(services.client_rpc_endpoint)
