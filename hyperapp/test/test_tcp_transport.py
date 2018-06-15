import logging
import time
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import asyncio
import pytest

from hyperapp.common import dict_coders, cdr_coders  # self-registering
from hyperapp.test.test_services import TestServices, TestClientServices
from hyperapp.test.server_process import ServerProcess

log = logging.getLogger()


TCP_ADDRESS = ('localhost', 8888)


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
    'common.ref_collector',
    'common.ref_registry',
    'common.tcp_packet',
    'server.request',
    'server.route_resolver',
    'server.transport.registry',
    'server.remoting',
    'server.transport.tcp',
    'server.echo_service',
    ]

client_code_module_list = [
    'common.ref',
    'common.ref_resolver',
    'common.ref_collector',
    'common.ref_registry',
    'common.tcp_packet',
    'client.async_ref_resolver',
    'client.capsule_registry',
    'client.transport.registry',
    'client.transport.tcp',
    ]


@pytest.fixture
def mp_pool():
    #multiprocessing.log_to_stderr()
    with multiprocessing.Pool(1) as pool:
        yield pool

@pytest.fixture
def thread_pool():
    with ThreadPoolExecutor(max_workers=1) as executor:
        yield executor

@pytest.fixture
def client_services(event_loop):
    return TestClientServices(type_module_list, client_code_module_list, event_loop)


class Server(ServerProcess):

    def __init__(self):
        self.services = TestServices(type_module_list, server_code_module_list, config)
        self.services.start()

    def stop(self):
        self.services.stop()
        assert not self.services.is_failed

        
async def client_send_packet(services):
    types = services.types
    address = types.tcp_transport.address(TCP_ADDRESS[0], TCP_ADDRESS[1])
    tcp_transport_ref = services.ref_registry.register_object(types.tcp_transport.address, address)
    transport = await services.transport_resolver.resolve(tcp_transport_ref)
    packet = services.types.test.packet(message='hello')
    ref = services.ref_registry.register_object(services.types.test.packet, packet)
    transport.send(ref)

@pytest.mark.asyncio
async def test_echo_must_respond_with_hello(event_loop, thread_pool, mp_pool, client_services):
    mp_pool.apply(Server.construct)
    await client_send_packet(client_services)
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
    bundle = bundle_t(ref, [capsule])

    packet = encode_tcp_packet(bundle, encoding)
    assert has_full_tcp_packet(packet)
    assert has_full_tcp_packet(packet + b'x')
    assert not has_full_tcp_packet(packet[:len(packet) - 1])
    decoded_bundle, packet_size = decode_tcp_packet(packet + b'xx')
    assert packet_size == len(packet)
    assert decoded_bundle == bundle
