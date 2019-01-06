import logging
import asyncio
import uuid

import pytest

from hyperapp.test.utils import resolve_type
from hyperapp.test.client_server_fixtures import (
    test_manager,
    queues,
    server_running,
    client_services_running,
    transport,
    transport_type_module_list,
    transport_server_code_module_list,
    transport_client_code_module_list,
    )

log = logging.getLogger(__name__)


type_module_list = [
    'test',
    ]

server_code_module_list = [
    'server.echo_service',
    ]


@pytest.fixture
def server(test_manager, queues, transport):
    with server_running(
            test_manager,
            queues,
            transport,
            transport_type_module_list(transport) + type_module_list,
            transport_server_code_module_list(transport) + server_code_module_list,
            ) as server:
        yield server


@pytest.fixture
def client_services(event_loop, queues, transport):
    with client_services_running(
            event_loop,
            queues,
            transport_type_module_list(transport) + type_module_list,
            transport_client_code_module_list(transport),
            ) as client_services:
        yield client_services


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
    test_error_t = resolve_type(services, 'test', 'test_error')
    # pytest.raises want argument conforming to inspect.isclass, but TExceptionClass is not
    with pytest.raises(Exception) as excinfo:
        await echo_proxy.fail('hello')
    assert isinstance(excinfo.value, test_error_t)
    assert excinfo.value.error_message == 'hello'


class NotificationService(object):

    def __init__(self):
        log.info('NotificationService is constructed')
        self.notify_future = asyncio.Future()

    def rpc_notify(self, request, message):
        log.info('NotificationService.notify: %r', message)
        self.notify_future.set_result(message)


async def echo_subscribe(services, echo_proxy):
    service_t = resolve_type(services, 'hyper_ref', 'service')
    echo_notificatoin_iface_ref = services.local_type_module_registry['test']['echo_notification_iface']
    service_id = str(uuid.uuid4())
    service = service_t(service_id, echo_notificatoin_iface_ref)
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


@pytest.mark.asyncio
async def test_call_echo(event_loop, queues, server, client_services, call_echo_fn):
    encoded_echo_service_bundle = server.extract_bundle('echo_service_ref')
    echo_service_ref = client_services.implant_bundle(encoded_echo_service_bundle)
    echo_proxy = await client_services.proxy_factory.from_ref(echo_service_ref)
    await call_echo_fn(client_services, echo_proxy)
