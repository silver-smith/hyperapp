import logging
from contextlib import contextmanager
import time
import multiprocessing
import pytest

from hyperapp.common import dict_coders, cdr_coders  # self-registering
from hyperapp.test.test_services import TestServices, TestClientServices

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
def client_services(event_loop):
    return TestClientServices(type_module_list, client_code_module_list, event_loop)

@contextmanager
def server_services():
    services = TestServices(type_module_list, server_code_module_list, config)
    services.start()
    yield services
    services.stop()


def server(started_barrier):
    with server_services() as services:
        started_barrier.wait()
        time.sleep(1)

        
async def client_send_packet(services, started_barrier):
    types = services.types
    address = types.tcp_transport.address(TCP_ADDRESS[0], TCP_ADDRESS[1])
    tcp_transport_ref = services.ref_registry.register_object(types.tcp_transport.address, address)
    started_barrier.wait()
    transport = await services.transport_resolver.resolve(tcp_transport_ref)
    packet = services.types.test.packet(message='hello')
    ref = services.ref_registry.register_object(services.types.test.packet, packet)
    transport.send(ref)

@pytest.mark.asyncio
async def test_packet_should_be_delivered(mp_pool, client_services):
    mp_manager = multiprocessing.Manager()
    started_barrier = mp_manager.Barrier(2)
    server_finished_result = mp_pool.apply_async(server, (started_barrier,))
    await client_send_packet(client_services, started_barrier)
    server_finished_result.get(timeout=3)


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
