import logging
import time

from .services import (
    endpoint_registry,
    generate_rsa_identity,
    partial_ref,
    rpc_endpoint_factory,
    )
from .tested.services import subprocess_rpc_server_running

log = logging.getLogger(__name__)


def test_subprocess_rpc_server():
    name = 'test-subprocess-rpc-server-main'
    identity = generate_rsa_identity(fast=True)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)
    with subprocess_rpc_server_running(name, rpc_endpoint, identity) as process:
        log.info("Started: %r", process)
        time.sleep(1)
        log.info("Stopping: %r", process)
    log.info("Stopped: %r", process)
