from functools import partial

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.module import Module

from .code_registry import CodeRegistry, CodeRegistryKeyError


async def adapter_factory(impl_registry, adapter_registry, piece):
    piece_t = deduce_value_type(piece)
    impl = impl_registry[piece_t]
    return await adapter_registry.animate(impl)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.adapter_registry = CodeRegistry('adapter', services.async_web, services.types)
        services.adapter_factory = partial(adapter_factory, services.impl_registry, services.adapter_registry)
