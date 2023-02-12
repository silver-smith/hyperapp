from .services import (
    endpoint_registry,
    rpc_endpoint_factory,
    server_identity,
    )


def init_server_rpc_endpoint():
    server_rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(server_identity, server_rpc_endpoint)
