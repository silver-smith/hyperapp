import logging
import time
import multiprocessing
from multiprocessing.managers import BaseManager
import concurrent.futures
import asyncio
import traceback
import pytest

from hyperapp.common import dict_coders, cdr_coders  # self-registering
from hyperapp.test.utils import encode_bundle, decode_bundle
from hyperapp.test.test_services import TestServerServices, TestClientServices

log = logging.getLogger()


TCP_ADDRESS = ('localhost', 7777)


config = {
    'transport.tcp': dict(bind_address=TCP_ADDRESS),
    }

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
    'common.route_resolver',
    'common.ref_collector',
    'common.ref_registry',
    'common.unbundler',
    'common.tcp_packet',
    'server.request',
    'server.transport.registry',
    'server.remoting',
    'server.transport.tcp',
    'server.echo_service',
    ]

client_code_module_list = [
    'common.ref',
    'common.ref_resolver',
    'common.route_resolver',
    'common.ref_collector',
    'common.ref_registry',
    'common.unbundler',
    'common.tcp_packet',
    'client.async_ref_resolver',
    'client.capsule_registry',
    'client.async_route_resolver',
    'client.endpoint_registry',
    'client.transport.registry',
    'client.remoting',
    'client.remoting_proxy',
    'client.transport.tcp',
    ]


class ServerServices(TestServerServices):

    def __init__(self, stopped_queue):
        super().__init__(type_module_list, server_code_module_list, config)
        self.stopped_queue = stopped_queue

    def on_stopped(self):
        log.info('ServerServices.on_stopped')
        self.stopped_queue.put(self.is_failed)


@pytest.fixture
def client_services(event_loop):
    return TestClientServices(type_module_list, client_code_module_list, event_loop)


class Server(object):

    def __init__(self, stopped_queue):
        self.services = ServerServices(stopped_queue)
        self.services.start()

    def stop(self):
        self.services.stop()
        assert not self.services.is_failed

    def make_echo_service_bundle(self):
        ref_collector = self.services.ref_collector_factory()
        echo_service_bundle = ref_collector.make_bundle([self.services.echo_service_ref])
        return encode_bundle(self.services, echo_service_bundle)


class TestManager(BaseManager):
    __test__ = False

TestManager.register('Server', Server)


@pytest.fixture
def test_manager():
    with TestManager() as manager:
        yield manager


@pytest.fixture
def stopped_queue():
    with multiprocessing.Manager() as manager:
        yield manager.Queue()

        
async def client_send_packet(services, encoded_echo_service_bundle):
    types = services.types

    echo_service_bundle = decode_bundle(services, encoded_echo_service_bundle)
    services.unbundler.register_bundle(echo_service_bundle)
    echo_service_ref = echo_service_bundle.roots[0]

    echo_proxy = await services.proxy_factory.from_ref(echo_service_ref)
    result = await echo_proxy.say('hello')
    assert result.response == 'hello'


def wait_for_server_stopped(stopped_queue):
    log.debug('wait_for_server_stopped.wait_for_queue: started')
    is_failed = stopped_queue.get()
    log.debug('wait_for_server_stopped.wait_for_queue: is_failed=%r', is_failed)
    assert not is_failed


@pytest.mark.asyncio
async def test_echo_must_respond_with_hello(event_loop, test_manager, stopped_queue, client_services):
    server = test_manager.Server(stopped_queue)
    encoded_echo_service_bundle = server.make_echo_service_bundle()
    server_stopped_future = event_loop.run_in_executor(None, wait_for_server_stopped, stopped_queue)
    await asyncio.wait([
        server_stopped_future,
        client_send_packet(client_services, encoded_echo_service_bundle),
        ], return_when=asyncio.FIRST_COMPLETED)
    log.debug('Test is finished, stopping the server now...')
    server.stop()


@pytest.mark.parametrize('encoding', ['json', 'cdr'])
def test_tcp_packet(client_services, encoding):
    from hyperapp.common.ref import make_ref, make_capsule
    from hyperapp.common.tcp_packet import has_full_tcp_packet, encode_tcp_packet, decode_tcp_packet
    test_packet_t = client_services.types.test.packet
    bundle_t = client_services.types.hyper_ref.bundle

    test_packet = test_packet_t(message='hello')
    capsule = make_capsule(test_packet_t, test_packet)
    ref = make_ref(capsule)
    bundle = bundle_t([ref], [capsule], [])

    packet = encode_tcp_packet(bundle, encoding)
    assert has_full_tcp_packet(packet)
    assert has_full_tcp_packet(packet + b'x')
    assert not has_full_tcp_packet(packet[:len(packet) - 1])
    decoded_bundle, packet_size = decode_tcp_packet(packet + b'xx')
    assert packet_size == len(packet)
    assert decoded_bundle == bundle
