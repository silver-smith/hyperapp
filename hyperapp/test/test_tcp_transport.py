import logging
from contextlib import contextmanager
import time
import multiprocessing
import pytest

from hyperapp.common import dict_coders, cdr_coders  # self-registering
from hyperapp.test.test_services import TestServices

log = logging.getLogger()


type_module_list = [
    'error',
    'resource',
    'core',
    'hyper_ref',
    'module',
    'packet',
    'phony_transport',
    'tcp_transport',
    'encrypted_transport',
    'test',
    ]

server_code_module_list = [
    'common.ref',
    'common.ref_resolver',
    'common.ref_collector',
    'common.ref_registry',
    'server.transport.registry',
    'server.transport.tcp',
    'server.request',
    'server.remoting',
    'server.echo_service',
    ]

client_code_module_list = [
    'common.ref',
    'common.ref_resolver',
    'common.ref_collector',
    'common.ref_registry',
    'client.async_ref_resolver',
    'client.piece_registry',
    'client.transport.registry',
    'client.transport.phony',
    'client.remoting_proxy',
    ]

config = {
    'transport.tcp': dict(bind_address=('localhost', 8888)),
    }

@pytest.fixture
def mp_pool():
    #multiprocessing.log_to_stderr()
    with multiprocessing.Pool(1) as pool:
        yield pool

@contextmanager
def server_services():
    services = TestServices(type_module_list, server_code_module_list, config)
    services.start()
    yield services
    services.stop()

def server():
    with server_services() as services:
        time.sleep(2)
        

@pytest.mark.asyncio
async def test_packet_should_be_delivered(mp_pool):
    mp_pool.apply(server)
