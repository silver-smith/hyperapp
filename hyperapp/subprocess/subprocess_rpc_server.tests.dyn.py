import logging
import time

from .tested.code import subprocess_rpc_server
from .code.subprocess_rpc_server_tests_aux import _callback

log = logging.getLogger(__name__)


def _test_subprocess_rpc_server_call():
    name = 'test-subprocess-rpc-server-main'
    identity = generate_rsa_identity(fast=True)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)
    with subprocess_rpc_server_running(name, rpc_endpoint, identity) as process:
        log.info("Started: %r", process)
        call = process.rpc_call(_callback)
        result = call()
        assert result == 'ok'
        log.info("Stopping: %r", process)
    log.info("Stopped: %r", process)


def _test_subprocess_rpc_server_submit():
    name = 'test-subprocess-rpc-server-main'
    identity = generate_rsa_identity(fast=True)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)
    with subprocess_rpc_server_running(name, rpc_endpoint, identity) as process:
        log.info("Started: %r", process)
        submit = process.rpc_submit(_callback)
        future = submit()
        assert future.result() == 'ok'
        log.info("Stopping: %r", process)
    log.info("Stopped: %r", process)
