import logging
import time

from .code.mark import mark
from .tested.code import subprocess_rpc_server

log = logging.getLogger(__name__)


def _callback():
    log.info("Test rpc subprocess callback is called")
    return 'ok'


@mark.fixture
def _sample_subprocess_rpc_server_tests_service():
    log.info("Test rpc subprocess sample service is called")
    return 'ok'


def test_subprocess_rpc_server_call(
        generate_rsa_identity, endpoint_registry, rpc_endpoint, subprocess_rpc_server_running):
    name = 'test-subprocess-rpc-server-main'
    identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(identity, rpc_endpoint)
    with subprocess_rpc_server_running(name, identity) as process:
        log.info("Started: %r", process)
        call = process.rpc_call(_callback)
        result = call()
        assert result == 'ok'
        log.info("Stopping: %r", process)
    log.info("Stopped: %r", process)


def test_subprocess_rpc_server_submit(
        generate_rsa_identity, endpoint_registry, rpc_endpoint, subprocess_rpc_server_running):
    name = 'test-subprocess-rpc-server-main'
    identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(identity, rpc_endpoint)
    with subprocess_rpc_server_running(name, identity) as process:
        log.info("Started: %r", process)
        submit = process.rpc_submit(_callback)
        future = submit()
        assert future.result() == 'ok'
        log.info("Stopping: %r", process)
    log.info("Stopped: %r", process)


def test_subprocess_rpc_server_service(
        generate_rsa_identity, endpoint_registry, rpc_endpoint, subprocess_rpc_server_running):
    name = 'test-subprocess-rpc-server-main'
    identity = generate_rsa_identity(fast=True)
    endpoint_registry.register(identity, rpc_endpoint)
    with subprocess_rpc_server_running(name, identity) as process:
        log.info("Started: %r", process)
        call = process.service_call('_sample_subprocess_rpc_server_tests_service')
        result = call()
        assert result == 'ok'
        log.info("Stopping: %r", process)
    log.info("Stopped: %r", process)
