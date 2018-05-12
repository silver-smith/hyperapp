import logging
from collections import namedtuple
import multiprocessing
import asyncio
import pytest

from hyperapp.common.identity import Identity
from hyperapp.common.packet_coders import packet_coders
from hyperapp.common import dict_coders, cdr_coders  # self-registering
from hyperapp.test.test_services import TestServices

log = logging.getLogger()


BUNDLE_ENCODING = 'json'


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
    'client.remoting',
    'client.remoting_proxy',
    ]


Queues = namedtuple('Queues', 'request response')


class Services(TestServices):

    def __init__(self, type_module_list, code_module_list, queues):
        self.request_queue = queues.request
        self.response_queue = queues.response
        super().__init__(type_module_list, code_module_list)


class ClientServices(Services):

    def __init__(self, type_module_list, code_module_list, queues, event_loop):
        self.request_queue = queues.request
        self.response_queue = queues.response
        self.event_loop = event_loop
        super().__init__(type_module_list, code_module_list, queues)


def encode_bundle(services, bundle):
    return packet_coders.encode(BUNDLE_ENCODING, bundle, services.types.hyper_ref.bundle)

def decode_bundle(services, encoded_bundle):
    return packet_coders.decode(BUNDLE_ENCODING, encoded_bundle, services.types.hyper_ref.bundle)


@pytest.fixture
def mp_pool():
    #multiprocessing.log_to_stderr()
    with multiprocessing.Pool(1) as pool:
        yield pool

@pytest.fixture
def queues():
    mp_manager = multiprocessing.Manager()
    return Queues(mp_manager.Queue(), mp_manager.Queue())

@pytest.fixture
def client_services(queues, event_loop):
    asyncio.get_event_loop().set_debug(True)
    services = ClientServices(type_module_list, client_code_module_list, queues, event_loop)
    services.start()
    yield services
    services.stop()


def make_transport_ref(services):
    types = services.types
    phony_transport_address = types.phony_transport.address()
    phony_transport_ref = services.ref_registry.register_object(types.phony_transport.address, phony_transport_address)
    identity = Identity.generate(fast=True)
    encrypted_transport_address = types.encrypted_transport.address(
        public_key_der=identity.public_key.to_der(),
        base_transport_ref=phony_transport_ref)
    encrypted_transport_ref = services.ref_registry.register_object(types.encrypted_transport.address, encrypted_transport_address)
    #return encrypted_transport_ref
    return phony_transport_ref

def server_make_echo_service_bundle(queues):
    services = Services(type_module_list, server_code_module_list, queues)
    transport_ref = make_transport_ref(services)
    href_types = services.types.hyper_ref
    service_ref = href_types.service_ref(['test', 'echo'], services.ECHO_SERVICE_ID, transport_ref)
    ref_resolver_ref = services.ref_registry.register_object(href_types.service_ref, service_ref)
    ref_collector = services.ref_collector_factory()
    echo_service_bundle = ref_collector.make_bundle(ref_resolver_ref)
    return encode_bundle(services, echo_service_bundle)

async def client_make_request_bundle(services, encoded_echo_service_bundle):
    echo_service_bundle = decode_bundle(services, encoded_echo_service_bundle)
    services.ref_registry.register_bundle(echo_service_bundle)
    echo_proxy = await services.proxy_factory.from_ref(echo_service_bundle.ref)
    result = await echo_proxy.say('hello')
    assert result.response == 'hello'

def server_process_request_bundle(queues):
    services = Services(type_module_list, server_code_module_list, queues)
    log.info('Server: picking request bundle:')
    encoded_request_bundle = services.request_queue.get(timeout=1)  # seconds
    log.info('Server: got request bundle')
    request_bundle = decode_bundle(services, encoded_request_bundle)
    services.ref_registry.register_bundle(request_bundle)
    service_response = services.transport_resolver.resolve(request_bundle.ref)
    service_response_ref = services.ref_registry.register_object(services.types.hyper_ref.service_response, service_response)
    ref_collector = services.ref_collector_factory()
    service_response_bundle = ref_collector.make_bundle(service_response_ref)
    encoded_response_bundle = encode_bundle(services, service_response_bundle)
    log.info('Server: putting response bundle...')
    services.response_queue.put(encoded_response_bundle)
    log.info('Server: finished.')

@pytest.mark.asyncio
async def test_echo_must_respond_with_hello(mp_pool, queues, client_services):
    encoded_echo_service_bundle = mp_pool.apply(server_make_echo_service_bundle, (queues,))
    mp_pool.apply_async(server_process_request_bundle, (queues,))
    encoded_request_bundle = await client_make_request_bundle(client_services, encoded_echo_service_bundle)
