from hyperapp.common.module import Module


class ThisModule(Module):

    async def async_init(self, services):
        services.client_rpc_endpoint = services.async_rpc_endpoint_factory()
        services.async_endpoint_registry.register(services.client_identity, services.client_rpc_endpoint)
