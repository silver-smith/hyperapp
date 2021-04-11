from hyperapp.common.module import Module


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)

    async def async_init(self, services):
        services.client_rpc_endpoint = services.async_rpc_endpoint()
        services.async_endpoint_registry.register(services.client_identity, services.client_rpc_endpoint)
