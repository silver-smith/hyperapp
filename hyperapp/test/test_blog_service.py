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


TEST_BLOG_ID = 'test_blog_service.blog'


type_module_list = [
    'text',
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
    'common.local_server_paths',
    'server.ponyorm_module',
    'server.ref_storage',
    'server.server_management',
    'server.blog',
    ]

client_code_module_list = [
    'client.object_registry',
    'client.objimpl_registry',
    'client.view',
#    'client.handle_resolver',
    'client.composite',
#    'client.form',
    'client.text_object',
    'client.column',
    'client.list_object',
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


class BlogObserver(object):

    def __init__(self):
        self.article_added_future = asyncio.Future()
        self.article_changed_future = asyncio.Future()
        self.article_deleted_future = asyncio.Future()

    def article_added(self, blog_id, article):
        self.article_added_future.set_result((blog_id, article))

    def article_changed(self, blog_id, article):
        self.article_changed_future.set_result((blog_id, article))

    def article_deleted(self, blog_id, article_id):
        self.article_deleted_future.set_result((blog_id, article_id))


async def pick_test_article(blog_service):
    chunk = await blog_service.fetch_blog_contents(TEST_BLOG_ID, from_key=None)
    if not chunk.items:
        pytest.skip('No test articles in blog_1')
    return chunk.items[0]


async def create_article(services, blog_service):
    observer = BlogObserver()
    await blog_service.add_observer(TEST_BLOG_ID, observer)
    article_id = await blog_service.create_article(TEST_BLOG_ID, 'title 1', 'text1 text1')
    assert article_id
    assert isinstance(article_id, int)
    # check notification is received
    blog_id, article = (await asyncio.wait_for(observer.article_added_future, timeout=3))
    assert blog_id == TEST_BLOG_ID
    # check article is actually created
    blog_service.invalidate_cache()
    assert article == (await blog_service.get_blog_item(TEST_BLOG_ID, article_id))


async def save_article(services, blog_service):
    article = await pick_test_article(blog_service)
    observer = BlogObserver()
    await blog_service.add_observer(TEST_BLOG_ID, observer)
    log.info('Saving article#%d', article.id)
    new_text = 'new text'
    await blog_service.save_article(TEST_BLOG_ID, article.id, article.title, new_text)
    blog_id, changed_article = (await asyncio.wait_for(observer.article_changed_future, timeout=3))
    assert blog_id == TEST_BLOG_ID
    assert changed_article.text == new_text

async def delete_article(services, blog_service):
    article = await pick_test_article(blog_service)
    observer = BlogObserver()
    await blog_service.add_observer(TEST_BLOG_ID, observer)
    log.info('Deleting article#%d', article.id)
    await blog_service.delete_article(TEST_BLOG_ID, article.id)
    blog_id, article_id = (await asyncio.wait_for(observer.article_deleted_future, timeout=3))
    assert blog_id == TEST_BLOG_ID
    assert article_id == article.id


async def fetch_blog_contents(services, blog_service):
    chunk = await blog_service.fetch_blog_contents(TEST_BLOG_ID, from_key=None)


async def get_blog_item(services, blog_service):
    article1 = await pick_test_article(blog_service)
    log.info('Requesting blog row for article#%d', article1.id)
    article2 = await blog_service.get_blog_item(TEST_BLOG_ID, article1.id)
    assert article1.id == article2.id


async def add_article_ref(services, blog_service):
    article = await pick_test_article(blog_service)
    log.info('Adding ref to article#%d', article.id)
    ref_id = await blog_service.add_ref(TEST_BLOG_ID, article.id, 'Test ref title', blog_service.to_ref())
    # check ref is actually created
    blog_service.invalidate_cache()
    ref_list = await blog_service.get_article_ref_list(TEST_BLOG_ID, article.id)
    ref = next(ref for ref in ref_list if ref.id == ref_id)
    assert ref.title == 'Test ref title'
    assert ref.ref == blog_service.to_ref()


async def update_article_ref(services, blog_service):
    article = await pick_test_article(blog_service)
    ref_list = await blog_service.get_article_ref_list(TEST_BLOG_ID, article.id)
    if not ref_list:
        pytest.skip('No test refs in blog_1 article#%d' % article.id)
    log.info('Updating ref to article#%d', article.id)
    ref_id = ref_list[0].id
    await blog_service.update_ref(TEST_BLOG_ID, article.id, ref_id, 'Changed ref title', blog_service.to_ref())
    # check ref is actually changed
    blog_service.invalidate_cache()
    ref_list = await blog_service.get_article_ref_list(TEST_BLOG_ID, article.id)
    ref = next(ref for ref in ref_list if ref.id == ref_id)
    assert ref.title == 'Changed ref title'


async def get_article_ref_list(services, blog_service):
    article = await pick_test_article(blog_service)
    ref_list = await blog_service.get_article_ref_list(TEST_BLOG_ID, article.id)
    if not ref_list:
        pytest.skip('No test refs in blog_1 article#%d' % article.id)


async def delete_article_ref(services, blog_service):
    article = await pick_test_article(blog_service)
    ref_list = await blog_service.get_article_ref_list(TEST_BLOG_ID, article.id)
    if not ref_list:
        pytest.skip('No test refs in blog_1 article#%d' % article.id)
    log.info('Updating ref to article#%d', article.id)
    ref_id = ref_list[0].id
    await blog_service.delete_ref(TEST_BLOG_ID, article.id, ref_id)
    # check ref is actually deleted
    blog_service.invalidate_cache()
    ref_list = await blog_service.get_article_ref_list(TEST_BLOG_ID, article.id)
    assert not any(ref for ref in ref_list if ref.id == ref_id)


@pytest.fixture(params=[
    create_article,
    save_article,
    delete_article,
    fetch_blog_contents,
    get_blog_item,
    add_article_ref,
    update_article_ref,
    get_article_ref_list,
    delete_article_ref,
    ])
def test_fn(request):
    return request.param


@pytest.mark.asyncio
async def test_call_blog(event_loop, queues, server, client_services, test_fn):
    encoded_blog_service_bundle = server.extract_bundle('blog_service_ref')
    blog_service_ref = client_services.implant_bundle(encoded_blog_service_bundle)
    blog_service = await client_services.blog_service_factory(blog_service_ref)
    await test_fn(client_services, blog_service)
