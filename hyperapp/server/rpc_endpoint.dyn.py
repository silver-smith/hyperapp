from hyperapp.common.module import Module


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.server_rpc_endpoint = services.rpc_endpoint()
        services.endpoint_registry.register(services.server_identity, services.server_rpc_endpoint)
