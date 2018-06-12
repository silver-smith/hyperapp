import logging
from collections import namedtuple
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import asyncio
import pytest
import traceback

from hyperapp.common.identity import Identity
from hyperapp.common.packet_coders import packet_coders
from hyperapp.common import dict_coders, cdr_coders  # self-registering
from hyperapp.test.test_services import TestServices, TestClientServices

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
    'client.capsule_registry',
    'client.route_resolver',
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


class ClientServices(TestClientServices):

    def __init__(self, type_module_list, code_module_list, event_loop, queues):
        self.request_queue = queues.request
        self.response_queue = queues.response
        super().__init__(type_module_list, code_module_list, event_loop)


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
def thread_pool():
    with ThreadPoolExecutor(max_workers=1) as executor:
        yield executor


class Server(object):

    instrance = None

    @classmethod
    def construct(cls, *args, **kw):
        cls.instance = cls(*args, **kw)

    @classmethod
    def _call(cls, method, *args, **kw):
        try:
            return method(cls.instance, *args, **kw)
        except:
            traceback.print_exc()
            raise

    @classmethod
    def call(cls, mp_pool, method, *args):
        return mp_pool.apply(cls._call, (method,) + args)

    @classmethod
    def call_async(cls, event_loop, thread_pool, mp_pool, method, *args):
        mp_future = mp_pool.apply_async(cls._call, (method,) + args)
        async_future = event_loop.create_future()
        def handle_result():
            log.debug('handle_result: started')
            try:
                result = mp_future.get(timeout=1)
                log.debug('handle_result: result=%r', result)
                event_loop.call_soon_threadsafe(async_future.set_result, result)
                log.debug('handle_result: succeeded')
            except Exception as x:
                log.debug('handle_result: exception')
                traceback.print_exc()
                event_loop.call_soon_threadsafe(async_future.set_exception, x)
        thread_pool.submit(handle_result)
        return async_future

    def __init__(self, queues):
        self.services = Services(type_module_list, server_code_module_list, queues)

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
        service_ref = href_types.service_ref(['test', 'echo'], self.services.ECHO_SERVICE_ID)
        service_ref_ref = self.services.ref_registry.register_object(href_types.service_ref, service_ref)
        ref_collector = self.services.ref_collector_factory()
        echo_service_bundle = ref_collector.make_bundle(service_ref_ref)
        return encode_bundle(self.services, echo_service_bundle)

    def process_request_bundle(self):
        log.info('Server: picking request bundle:')
        encoded_request_bundle = self.services.request_queue.get(timeout=1)  # seconds
        log.info('Server: got request bundle')
        request_bundle = decode_bundle(self.services, encoded_request_bundle)
        self.services.ref_registry.register_bundle(request_bundle)
        service_response = self.services.transport_resolver.resolve(request_bundle.ref)
        service_response_ref = self.services.ref_registry.register_object(self.services.types.hyper_ref.service_response, service_response)
        ref_collector = self.services.ref_collector_factory()
        service_response_bundle = ref_collector.make_bundle(service_response_ref)
        encoded_response_bundle = encode_bundle(self.services, service_response_bundle)
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
    asyncio.get_event_loop().set_debug(True)
    services = ClientServices(type_module_list, client_code_module_list, event_loop, queues)
    services.start()
    yield services
    services.stop()


async def client_make_phony_transport_ref(services):
    types = services.types
    phony_transport_address = types.phony_transport.address()
    return services.ref_registry.register_object(types.phony_transport.address, phony_transport_address)

async def client_make_request_bundle(services, transport_ref, encoded_echo_service_bundle):
    phony_transport_ref = await client_make_phony_transport_ref(services)
    echo_service_bundle = decode_bundle(services, encoded_echo_service_bundle)
    services.ref_registry.register_bundle(echo_service_bundle)
    services.route_registry.register(echo_service_bundle.ref, transport_ref)
    echo_proxy = await services.proxy_factory.from_ref(echo_service_bundle.ref)
    result = await echo_proxy.say('hello')
    assert result.response == 'hello'

@pytest.mark.asyncio
async def test_echo_must_respond_with_hello(event_loop, thread_pool, mp_pool, queues, client_services):
    mp_pool.apply(Server.construct, (queues,))
    transport_ref = Server.call(mp_pool, Server.make_transport_ref)
    encoded_echo_service_bundle = Server.call(mp_pool, Server.make_echo_service_bundle)
    async_future = Server.call_async(event_loop, thread_pool, mp_pool, Server.process_request_bundle)
    encoded_request_bundle = await asyncio.gather(
        client_make_request_bundle(client_services, transport_ref, encoded_echo_service_bundle),
        async_future,
        )
