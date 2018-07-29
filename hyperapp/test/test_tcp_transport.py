import logging
import time
import multiprocessing
import concurrent.futures
import asyncio
import traceback
import pytest

from hyperapp.common import dict_coders, cdr_coders  # self-registering
from hyperapp.test.utils import encode_bundle, decode_bundle
from hyperapp.test.test_services import TestServerServices, TestClientServices
from hyperapp.test.server_process import mp2async_future, ServerProcess

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
def mp_pool():
    #multiprocessing.log_to_stderr()
    # only 1 worker is expected by ServerProcess
    with multiprocessing.Pool(1) as pool:
        yield pool

@pytest.fixture
def thread_pool():
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        yield executor

@pytest.fixture
def client_services(event_loop):
    return TestClientServices(type_module_list, client_code_module_list, event_loop)


class Server(ServerProcess):

    def __init__(self, stopped_queue):
        self.services = ServerServices(stopped_queue)
        self.services.start()

    def stop(self):
        self.services.stop()
        assert not self.services.is_failed

    def make_echo_service_bundle(self):
        href_types = self.services.types.hyper_ref
        service = href_types.service(self.services.ECHO_SERVICE_ID, ['test', 'echo'])
        service_ref = self.services.ref_registry.register_object(href_types.service, service)
        ref_collector = self.services.ref_collector_factory()
        echo_service_bundle = ref_collector.make_bundle([service_ref])
        return encode_bundle(self.services, echo_service_bundle)

        
async def client_send_packet(services, encoded_echo_service_bundle):
    types = services.types

    echo_service_bundle = decode_bundle(services, encoded_echo_service_bundle)
    services.ref_registry.register_bundle(echo_service_bundle)

    address = types.tcp_transport.address(TCP_ADDRESS[0], TCP_ADDRESS[1])
    tcp_transport_ref = services.ref_registry.register_object(types.tcp_transport.address, address)
    services.route_registry.register(echo_service_bundle.roots[0], tcp_transport_ref)

    echo_proxy = await services.proxy_factory.from_ref(echo_service_bundle.roots[0])
    result = await echo_proxy.say('hello')
    assert result.response == 'hello'


def wait_for_server_stopped(thread_pool, stopped_queue):
    mp_future = concurrent.futures.Future()
    def wait_for_queue():
        log.debug('wait_for_server_stopped.wait_for_queue: started')
        try:
            is_failed = stopped_queue.get()
            log.debug('wait_for_server_stopped.wait_for_queue: is_failed=%r', is_failed)
            assert not is_failed
            mp_future.set_result(None)
            log.debug('wait_for_server_stopped.wait_for_queue: succeeded')
        except Exception as x:
            log.exception('wait_for_server_stopped.wait_for_queue:')
            mp_future.set_exception(x)
    thread_pool.submit(wait_for_queue)
    return mp_future


@pytest.mark.asyncio
async def test_echo_must_respond_with_hello(event_loop, thread_pool, mp_pool, client_services):
    mp_manager = multiprocessing.Manager()
    stopped_queue = mp_manager.Queue()
    mp_pool.apply(Server.construct, (stopped_queue,))
    encoded_echo_service_bundle = Server.call(mp_pool, Server.make_echo_service_bundle)
    await asyncio.wait([
        mp2async_future(event_loop, thread_pool, wait_for_server_stopped(thread_pool, stopped_queue)),
        client_send_packet(client_services, encoded_echo_service_bundle),
        ], return_when=asyncio.FIRST_COMPLETED)
    log.debug('Test is finished, stopping the server now...')
    Server.call(mp_pool, Server.stop)


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
