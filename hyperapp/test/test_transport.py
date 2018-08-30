import logging
from collections import namedtuple
import multiprocessing
from multiprocessing.managers import BaseManager
import asyncio
import uuid

import pytest

from hyperapp.common.init_logging import init_logging
from hyperapp.test.utils import log_exceptions, encode_bundle, decode_bundle
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
    'common.visual_rep',
    'common.ref_resolver',
    'common.route_resolver',
    'common.ref_collector',
    'common.ref_registry',
    'common.unbundler',
    'common.tcp_packet',
    'server.transport.registry',
    'server.request',
    'server.remoting',
    'server.remoting_proxy',
    'server.echo_service',
    ]

client_code_module_list = [
    'common.ref',
    'common.visual_rep',
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
    'client.service_registry',
    'client.transport.registry',
    'client.request',
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

    def __init__(self, type_module_list, code_module_list, queues):
        # queues are used by phony transport module
        self.request_queue = queues.request
        self.response_queue = queues.response
        super().__init__(type_module_list, code_module_list)


class Server(object, metaclass=log_exceptions):

    def __init__(self, transport, queues):
        init_logging('test.yaml')
        code_module_list = server_code_module_list + [
            'server.transport.%s' % transport,
            ]
        self.services = ServerServices(type_module_list, code_module_list, queues)
        self.services.start()

    def stop(self):
        self.services.stop()
        assert not self.services.is_failed

    def make_echo_service_bundle(self):
        from hyperapp.common.visual_rep import pprint

        ref_collector = self.services.ref_collector_factory()
        echo_service_bundle = ref_collector.make_bundle([self.services.echo_service_ref])
        pprint(echo_service_bundle, title='Echo service bundle:')
        return encode_bundle(self.services, echo_service_bundle)


class TestManager(BaseManager):
    __test__ = False

TestManager.register('Server', Server)

@pytest.fixture
def test_manager():
    with TestManager() as manager:
        yield manager


@pytest.fixture(params=['phony', 'tcp'])
def transport(request):
    return request.param

@pytest.fixture
def server(test_manager, queues, transport):
    server = test_manager.Server(transport, queues)
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
    init_logging('test.yaml')
    services = ClientServices(type_module_list, client_code_module_list, event_loop, queues)
    services.start()
    yield services
    services.stop()


async def echo_say(services, echo_proxy):
    result = await echo_proxy.say('hello')
    assert result.response == 'hello'

async def echo_eat(services, echo_proxy):
    result = await echo_proxy.eat('hello')
    assert result

async def echo_notify(services, echo_proxy):
    result = await echo_proxy.notify('hello')
    assert result is None

async def echo_fail(services, echo_proxy):
    # pytest.raises want argument conforming to inspect.isclass, but TExceptionClass is not
    with pytest.raises(Exception) as excinfo:
        await echo_proxy.fail('hello')
    assert isinstance(excinfo.value, services.types.test.test_error)
    assert excinfo.value.error_message == 'hello'


class NotificationService(object):

    def __init__(self):
        log.info('NotificationService is constructed')
        self.notify_future = asyncio.Future()

    def rpc_notify(self, request, message):
        log.info('NotificationService.notify: %r', message)
        self.notify_future.set_result(message)


async def echo_subscribe(services, echo_proxy):
    service_id = str(uuid.uuid4())
    service = services.types.hyper_ref.service(service_id, ['test', 'echo_notification_iface'])
    service_ref = services.ref_registry.register_object(service)
    notification_service = NotificationService()
    services.service_registry.register(service_ref, lambda: notification_service)
    await echo_proxy.subscribe(service_ref)
    await echo_proxy.broadcast('hello')
    log.info('Waiting for notification:')
    message = (await asyncio.wait_for(notification_service.notify_future, timeout=3))
    log.info('Waiting for notification: got it: %r', message)
    assert message == 'hello'

@pytest.fixture(params=[echo_say, echo_eat, echo_notify, echo_fail, echo_subscribe])
def call_echo_fn(request):
    return request.param


async def client_call_echo_say_service(services, call_echo_fn, encoded_echo_service_bundle):
    echo_service_bundle = decode_bundle(services, encoded_echo_service_bundle)
    services.unbundler.register_bundle(echo_service_bundle)
    echo_service_ref = echo_service_bundle.roots[0]
    echo_proxy = await services.proxy_factory.from_ref(echo_service_ref)
    await call_echo_fn(services, echo_proxy)

@pytest.mark.asyncio
async def test_call_echo(event_loop, queues, server, client_services, call_echo_fn):
    encoded_echo_service_bundle = server.make_echo_service_bundle()
    await client_call_echo_say_service(client_services, call_echo_fn, encoded_echo_service_bundle)
