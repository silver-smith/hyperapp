from .services import (
    endpoint_registry,
    generate_rsa_identity,
    rpc_call_factory,
    rpc_endpoint_factory,
    )


def call_back(tcp_master_peer, master_fn_ref):
    rpc_endpoint = rpc_endpoint_factory()
    my_identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(my_identity, rpc_endpoint)
    rpc_call = rpc_call_factory(rpc_endpoint, tcp_master_peer, master_fn_ref, my_identity)
    rpc_call("hello")
