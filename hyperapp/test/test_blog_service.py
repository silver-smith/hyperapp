import logging
import asyncio
from unittest.mock import Mock, MagicMock

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


TEST_BLOG = 'test_blog_service.blog'


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


async def pick_test_article(blog_service):
    chunk = await blog_service.fetch_blog_contents(TEST_BLOG, sort_column_id='id', from_key=None, desc_count=0, asc_count=100)
    if not chunk.rows:
        pytest.skip('No test articles in blog_1')
    return chunk.rows[0]


class BlogObserver(object):

    def __init__(self):
        self.article_added_future = asyncio.Future()

    def article_added(self, blog_id, article):
        self.article_added_future.set_result((blog_id, article))


async def blog_create_article(services, blog_service):
    observer = BlogObserver()
    await blog_service.add_observer(TEST_BLOG, observer)
    article_id = await blog_service.create_article(TEST_BLOG, 'title 1', 'text1 text1')
    assert article_id
    assert isinstance(article_id, int)
    blog_id, article = (await asyncio.wait_for(observer.article_added_future, timeout=3))
    assert blog_id == TEST_BLOG
    assert article == (await blog_service.get_blog_row(TEST_BLOG, article_id))

async def blog_save_article(services, blog_service):
    article = await pick_test_article(blog_service)
    log.info('Saving article#%d', article.id)
    await blog_service.save_article(TEST_BLOG, article.id, article.title, 'text2 text2')

async def blog_fetch_blog_contents(services, blog_service):
    chunk = await blog_service.fetch_blog_contents(TEST_BLOG, sort_column_id='id', from_key=None, desc_count=0, asc_count=100)

async def blog_get_blog_row(services, blog_service):
    article1 = await pick_test_article(blog_service)
    log.info('Requesting blog row for article#%d', article1.id)
    article2 = await blog_service.get_blog_row(TEST_BLOG, article1.id)
    assert article1.id == article2.id

async def blog_get_article_ref_list(services, blog_service):
    ref_list = await blog_service.get_article_ref_list(TEST_BLOG, article_id)


@pytest.fixture(params=[blog_create_article, blog_save_article, blog_fetch_blog_contents, blog_get_blog_row])
def test_fn(request):
    return request.param


@pytest.mark.asyncio
async def test_call_echo(event_loop, queues, server, client_services, test_fn):
    encoded_blog_service_bundle = server.extract_bundle('blog_service_ref')
    blog_service_ref = client_services.implant_bundle(encoded_blog_service_bundle)
    blog_service = await client_services.blog_service_factory(blog_service_ref)
    await test_fn(client_services, blog_service)
