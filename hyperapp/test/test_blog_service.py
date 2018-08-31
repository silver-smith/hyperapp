import logging
import asyncio

import pytest

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
    'object_selector',
    'text_object',
    'form',
    'blog',
    ]

server_type_module_list = [
    'ref_list',
    ]

client_type_module_list = [
    'line_object',
    ]

server_code_module_list = [
    'server.ponyorm_module',
    'server.ref_storage',
    'server.server_management',
    'server.blog',
    ]

client_code_module_list = [
    'client.objimpl_registry',
    'client.view_registry',
    'client.handle_resolver',
    'client.object_selector',
    'client.form',
    'client.text_object',
    'client.blog',
    ]


@pytest.fixture
def server(test_manager, queues, transport):
    with server_running(
            test_manager,
            queues,
            transport,
            transport_type_module_list(transport) + type_module_list + server_type_module_list,
            transport_server_code_module_list(transport) + server_code_module_list,
            ) as server:
        yield server


@pytest.fixture
def client_services(event_loop, queues, transport):
    with client_services_running(
            event_loop,
            queues,
            transport_type_module_list(transport) + type_module_list + client_type_module_list,
            transport_client_code_module_list(transport) + client_code_module_list,
            ) as client_services:
        yield client_services


async def blog_create_article(services, blog_service):
    article_id = await blog_service.create_article('blog_1', 'title 1', 'text\ntext\n1')
    assert article_id
    assert isinstance(article_id, int)


@pytest.fixture(params=[blog_create_article])
def test_fn(request):
    return request.param


async def create_blog_service(blog_service_ref, proxy_factory):
    from hyperapp.client.blog import BlogService

    return (await BlogService.from_data(blog_service_ref, proxy_factory))

@pytest.mark.asyncio
async def test_call_echo(event_loop, queues, server, client_services, test_fn):
    encoded_blog_service_bundle = server.extract_bundle('blog_service_ref')
    blog_service_ref = client_services.implant_bundle(encoded_blog_service_bundle)
    blog_service = await create_blog_service(blog_service_ref, client_services.proxy_factory)
    await test_fn(client_services, blog_service)
