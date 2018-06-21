import logging
from collections import namedtuple
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import asyncio
import pytest
import traceback

from hyperapp.common.identity import Identity
from hyperapp.common import dict_coders, cdr_coders  # self-registering
from hyperapp.test.utils import encode_bundle, decode_bundle
from hyperapp.test.test_services import TestServerServices, TestClientServices
from hyperapp.test.server_process import ServerProcess

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
    'server.route_resolver',
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
    'client.capsule_registry',
    'client.route_resolver',
    'client.endpoint_registry',
    'client.transport.registry',
    'client.remoting',
    'client.remoting_proxy',
    'client.transport.phony',
    ]


Queues = namedtuple('Queues', 'request response')


class ServerServices(TestServerServices):

    def __init__(self, type_module_list, code_module_list, queues):
        self.request_queue = queues.request
        self.response_queue = queues.response
        super().__init__(type_module_list, code_module_list)


class ClientServices(TestClientServices):

    def __init__(self, type_module_list, code_module_list, event_loop, queues):
        self.request_queue = queues.request
        self.response_queue = queues.response
        super().__init__(type_module_list, code_module_list, event_loop)


@pytest.fixture
def mp_pool():
    #multiprocessing.log_to_stderr()
    with multiprocessing.Pool(1) as pool:
        yield pool

@pytest.fixture
def thread_pool():
    with ThreadPoolExecutor(max_workers=1) as executor:
        yield executor


class Server(ServerProcess):

    def __init__(self, queues):
        self.services = ServerServices(type_module_list, server_code_module_list, queues)

    def make_transport_ref(self):
        types = self.services.types
        phony_transport_address = types.phony_transport.address()
        phony_transport_ref = self.services.ref_registry.register_object(types.phony_transport.address, phony_transport_address)
        identity = Identity.generate(fast=True)
        encrypted_transport_address = types.encrypted_transport.address(
            public_key_der=identity.public_key.to_der(),
            base_transport_ref=phony_transport_ref)
        encrypted_transport_ref = self.services.ref_registry.register_object(types.encrypted_transport.address, encrypted_transport_address)
        #return encrypted_transport_ref
        return phony_transport_ref

    def make_echo_service_bundle(self):
        href_types = self.services.types.hyper_ref
        service = href_types.service(self.services.ECHO_SERVICE_ID, ['test', 'echo'])
        service_ref = self.services.ref_registry.register_object(href_types.service, service)
        ref_collector = self.services.ref_collector_factory()
        echo_service_bundle = ref_collector.make_bundle([service_ref])
        return encode_bundle(self.services, echo_service_bundle)

    def process_request_bundle(self):
        from hyperapp.common.ref import decode_capsule
        types = self.services.types

        log.info('Server: picking request bundle:')
        encoded_request_bundle = self.services.request_queue.get(timeout=1)  # seconds
        log.info('Server: got request bundle')

        # decode bundle
        request_bundle = decode_bundle(self.services, encoded_request_bundle)
        self.services.ref_registry.register_bundle(request_bundle)
        rpc_request_capsule = self.services.ref_resolver.resolve_ref(request_bundle.roots[0])
        rpc_request = decode_capsule(self.services.types, rpc_request_capsule)

        # resolve transport
        local_transport_ref = self.services.ref_registry.register_object(types.hyper_ref.local_transport_address, types.hyper_ref.local_transport_address())
        local_transport = self.services.transport_resolver.resolve(local_transport_ref)

        # handle request
        rpc_response = local_transport._process_request(rpc_request)

        # encode response
        rpc_response_ref = self.services.ref_registry.register_object(self.services.types.hyper_ref.rpc_message, rpc_response)
        ref_collector = self.services.ref_collector_factory()
        rpc_response_bundle = ref_collector.make_bundle([rpc_response_ref])
        encoded_response_bundle = encode_bundle(self.services, rpc_response_bundle)
        log.info('Server: putting response bundle...')
        self.services.response_queue.put(encoded_response_bundle)
        log.info('Server: finished.')


@pytest.fixture
def queues():
    mp_manager = multiprocessing.Manager()
    return Queues(mp_manager.Queue(), mp_manager.Queue())

@pytest.fixture
def server_process():
    with ServerProcess() as sp:
        yield sp
    
@pytest.fixture
def client_services(queues, event_loop):
    event_loop.set_debug(True)
    services = ClientServices(type_module_list, client_code_module_list, event_loop, queues)
    services.start()
    yield services
    services.stop()


async def client_make_phony_transport_ref(services):
    types = services.types
    phony_transport_address = types.phony_transport.address()
    return services.ref_registry.register_object(types.phony_transport.address, phony_transport_address)

async def client_call_echo_service(services, transport_ref, encoded_echo_service_bundle):
    phony_transport_ref = await client_make_phony_transport_ref(services)
    echo_service_bundle = decode_bundle(services, encoded_echo_service_bundle)
    services.ref_registry.register_bundle(echo_service_bundle)
    services.route_registry.register(echo_service_bundle.roots[0], transport_ref)
    echo_proxy = await services.proxy_factory.from_ref(echo_service_bundle.roots[0])
    result = await echo_proxy.say('hello')
    assert result.response == 'hello'

@pytest.mark.asyncio
async def test_echo_must_respond_with_hello(event_loop, thread_pool, mp_pool, queues, client_services):
    mp_pool.apply(Server.construct, (queues,))
    transport_ref = Server.call(mp_pool, Server.make_transport_ref)
    encoded_echo_service_bundle = Server.call(mp_pool, Server.make_echo_service_bundle)
    async_future = Server.async_call(event_loop, thread_pool, mp_pool, Server.process_request_bundle)
    encoded_request_bundle = await asyncio.gather(
        client_call_echo_service(client_services, transport_ref, encoded_echo_service_bundle),
        async_future,
        )
