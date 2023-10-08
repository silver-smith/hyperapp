from contextlib import contextmanager

from .services import (
    endpoint_registry,
    generate_rsa_identity,
    rpc_endpoint_factory,
    subprocess_rpc_server_running,
    )


@contextmanager
def subprocess(process_name, rpc_timeout):
    identity = generate_rsa_identity(fast=True)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)
    with subprocess_rpc_server_running(
            process_name,
            rpc_endpoint,
            identity,
            timeout_sec=rpc_timeout,
        ) as process:
        yield process
