import logging
from collections import namedtuple
import multiprocessing
from multiprocessing.managers import BaseManager
from concurrent.futures import ThreadPoolExecutor
import asyncio
import pytest

from hyperapp.common.visual_rep import pprint
from hyperapp.test.utils import encode_bundle, decode_bundle
from hyperapp.test.test_services import TestServerServices, TestClientServices

log = logging.getLogger(__name__)


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
    'server.transport.registry',
    'server.request',
    'server.remoting',
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
    'client.transport.phony',
    'client.transport.tcp',
    ]


Queues = namedtuple('Queues', 'request response')


@pytest.fixture
def queues():
    with multiprocessing.Manager() as manager:
        yield Queues(manager.Queue(), manager.Queue())


class ServerServices(TestServerServices):

    def __init__(self, type_module_list, code_module_list, stopped_queue, queues):
        # queues are used by phony transport module
        self.request_queue = queues.request
        self.response_queue = queues.response
        super().__init__(type_module_list, code_module_list)
        self.stopped_queue = stopped_queue

    def on_stopped(self):
        log.info('ServerServices.on_stopped')
        self.stopped_queue.put(self.is_failed)


class Server(object):

    def __init__(self, transport, stopped_queue, queues):
        code_module_list = server_code_module_list + [
            'server.transport.%s' % transport,
            ]
        self.services = ServerServices(type_module_list, code_module_list, stopped_queue, queues)
        self.services.start()

    def stop(self):
        self.services.stop()
        assert not self.services.is_failed

    def make_echo_service_bundle(self):
        ref_collector = self.services.ref_collector_factory()
        echo_service_bundle = ref_collector.make_bundle([self.services.echo_service_ref])
        log.info('Echo service bundle:')
        pprint(self.services.types.hyper_ref.bundle, echo_service_bundle)
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

@pytest.fixture(params=['phony', 'tcp'])
def transport(request):
    return request.param

@pytest.fixture
def server(test_manager, stopped_queue, queues, transport):
    server = test_manager.Server(transport, stopped_queue, queues)
    yield server
    log.debug('Test is finished, stopping the server now...')
    server.stop()


class ClientServices(TestClientServices):

    def __init__(self, type_module_list, code_module_list, event_loop, queues):
        # queues are used by phony transport module
        self.request_queue = queues.request
        self.response_queue = queues.response
        super().__init__(type_module_list, code_module_list, event_loop)


@pytest.fixture
def client_services(queues, event_loop):
    event_loop.set_debug(True)
    services = ClientServices(type_module_list, client_code_module_list, event_loop, queues)
    services.start()
    yield services
    services.stop()


async def call_echo_say(echo_proxy):
    result = await echo_proxy.say('hello')
    assert result.response == 'hello'

async def call_echo_eat(echo_proxy):
    result = await echo_proxy.eat('hello')
    assert result

@pytest.fixture(params=[call_echo_say, call_echo_eat])
def call_echo_fn(request):
    return request.param


def wait_for_server_stopped(stopped_queue):
    log.debug('wait_for_server_stopped.wait_for_queue: started')
    is_failed = stopped_queue.get()
    log.debug('wait_for_server_stopped.wait_for_queue: is_failed=%r', is_failed)
    assert not is_failed

async def client_call_echo_say_service(services, call_echo_fn, encoded_echo_service_bundle):
    echo_service_bundle = decode_bundle(services, encoded_echo_service_bundle)
    services.unbundler.register_bundle(echo_service_bundle)
    echo_service_ref = echo_service_bundle.roots[0]
    echo_proxy = await services.proxy_factory.from_ref(echo_service_ref)
    await call_echo_fn(echo_proxy)


@pytest.mark.asyncio
async def test_call_echo(event_loop, queues, stopped_queue, server, client_services, call_echo_fn):
    encoded_echo_service_bundle = server.make_echo_service_bundle()
    server_stopped_future = event_loop.run_in_executor(None, wait_for_server_stopped, stopped_queue)
    encoded_request_bundle = await asyncio.wait([
        server_stopped_future,
        client_call_echo_say_service(client_services, call_echo_fn, encoded_echo_service_bundle),
        ], return_when=asyncio.FIRST_COMPLETED)
