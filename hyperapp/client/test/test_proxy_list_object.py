import os.path
import logging
import uuid
from itertools import chain
from unittest import mock
import aiomock
import asyncio
import pytest
from hyperapp.common.htypes import tInt
from hyperapp.common.htypes.list_interface import Column, ListInterface
from hyperapp.common.list_object import Element, Chunk, ListDiff
from hyperapp.common.identity import PublicKey
from hyperapp.common.services import ServicesBase
from hyperapp.client.request import Request
from hyperapp.client.server import Server
from hyperapp.client.list_object import ListObserver
from hyperapp.client.proxy_list_object import ProxyListObject

log = logging.getLogger(__name__)


class Services(ServicesBase):

    def __init__(self):
        self.interface_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../common/interface'))
        ServicesBase.init_services(self)
        self._load_type_modules([
                'resource',
                'packet',
                'core',
                ])


# override pytest-asyncio event_loop to test-scoped, or it will be still running and run_until_complete from other tests will fail
@pytest.fixture
def event_loop():
    return asyncio.get_event_loop()

@pytest.fixture
def services():
    return Services()


public_key_pem = '''
-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAypQ+wUX1tb2s74JeoPSNAHOj5zLGpnTnKUB+cYFzjAjUX+SXt39cH7tMcYPj7uLsn5LfSf3sit+Z9yQEcZuY
U7Bd3vjwx6TTnwQfBpmJKTE2mgctNM1AiO6GB1GsKDcj7PwKqnl5TJXOyppWvKWPNauWqxlTS1aCi236AnjbfZE93UFgHFQ55XVbWUUA4fz96Q/Xmr1TlwjKf9+ZYL1J
6JTu1ec2r4K/lCgiQLqX46tVXAmRWjFtbC5nB1buVwN6L4g5a6r5uwOMCL9gGbuFNmQuC2hRlrRO6gFFNchIh/hYxnhzf0jm13CbspdVza9IHBvy8yoEX+tlVd/Wkxu3
ixRPUdD7vASellSRp/YkbJX3IdEIuG9J4XLIc6m3d57qnUwuQSoHxl+CyoCf4NV6vETpVIURuD9gvfuSUjsK2nM5JhtvnpGi6F1X9Ydh8qx84S9fGPNz4o1PgubLyjyL
vwWhRqfwx2ryXNQwc2r1LjsoKmWnEjmrayzrqcRbgjNxSJsWm2h5KP3lHl5vEct7wW5UhvHquE5JqJ7vfz2kSOoERF2N08CBjtXb1JuepFzzfOCVs959hi48LWE7ud1E
M6nlQe0Uf0B0rUKTvBnXI7Y5wrHnZkAHEvjOqj+RYiRD13f+yUOnpMaWB+s1GqGFeKiI58a13Vd/GBKUcEGVk0UCAwEAAQ==
-----END PUBLIC KEY-----
'''

@pytest.fixture
def server():
    public_key = PublicKey.from_pem(public_key_pem)
    server = aiomock.AIOMock(
        spec=Server,
        public_key=public_key)
    server.send_notification.async_return_value = None
    return server


test_iface = ListInterface('test_iface', columns=[Column('id', type=tInt, is_key=True)])


class StubCacheRepository(object):

    def __init__(self):
        self._map = {}

    def load_value(self, key, t):
        return self._map.get(tuple(key))

    def store_value(self, key, value, t):
        assert isinstance(value, t), repr(value)
        self._map[tuple(key)] = value


@pytest.fixture
def proxy_list_object(services, server):
    resources_manager = mock.Mock()
    resources_manager.resove.return_value = None
    param_editor_registry = mock.Mock()
    test_iface.register_types(services.types.core)
    return ProxyListObject(
        services.types.packet,
        services.types.core,
        services.iface_registry,
        StubCacheRepository(),
        resources_manager,
        param_editor_registry,
        server,
        ['test-path'],
        test_iface,
        )


@pytest.mark.asyncio
@asyncio.coroutine
def test_fetch_elements(proxy_list_object):
    elements = [Element(i, test_iface.Row(i)) for i in range(10)]
    fetch_result = test_iface.Contents(
        chunk=Chunk(
            sort_column_id='id',
            from_key=None,
            elements=elements,
            bof=True,
            eof=True,
            ).to_data(test_iface))
    response = mock.Mock(error=None, result=fetch_result)
    proxy_list_object.server.execute_request.async_return_value = response
    observer = mock.Mock(spec=ListObserver)
    proxy_list_object.subscribe(observer)
    chunk = yield from proxy_list_object.fetch_elements('id', None, 0, 100)
    assert chunk.bof
    assert chunk.eof
    assert chunk.elements == elements
    observer.process_fetch_result.assert_called_once_with(chunk)


@pytest.mark.asyncio
@asyncio.coroutine
def test_fetch_cached_elements(proxy_list_object):
    elements = [Element(i, test_iface.Row(i)) for i in range(10)]
    fetch_result = test_iface.Contents(
        chunk=Chunk(
            sort_column_id='id',
            from_key=None,
            elements=elements,
            bof=True,
            eof=True,
            ).to_data(test_iface))
    response = mock.Mock(error=None, result=fetch_result)
    proxy_list_object.server.execute_request.async_return_value = response
    yield from proxy_list_object.fetch_elements('id', None, 0, 100)
    observer = mock.Mock(spec=ListObserver)
    proxy_list_object.subscribe(observer)
    proxy_list_object.server.reset_mock()
    # second call must fetch results from cache (actual slices), server must not be called
    chunk = yield from proxy_list_object.fetch_elements('id', None, 0, 10)
    assert chunk.bof
    assert chunk.eof
    assert chunk.elements == elements
    observer.process_fetch_result.assert_called_once_with(chunk)
    proxy_list_object.server.execute_request.assert_not_called()


# two adjacent chunks must be merged when fetch results are processed
@pytest.mark.asyncio
@asyncio.coroutine
def test_chunks_are_merged(services, proxy_list_object):
    # fetch first 10 elements
    fetch_result = test_iface.Contents(
        chunk=Chunk(
            sort_column_id='id',
            from_key=None,
            elements=[Element(i, test_iface.Row(i)) for i in range(10)],
            bof=True,
            eof=False,
            ).to_data(test_iface))
    response = mock.Mock(error=None, result=fetch_result)
    proxy_list_object.server.execute_request.async_return_value = response
    yield from proxy_list_object.fetch_elements('id', None, 0, 100)

    # fetch next 10 elements
    fetch_result = test_iface.Contents(
        chunk=Chunk(
            sort_column_id='id',
            from_key=9,
            elements=[Element(i, test_iface.Row(i)) for i in range(10, 20)],
            bof=False,
            eof=False,
            ).to_data(test_iface))
    response = mock.Mock(error=None, result=fetch_result)
    proxy_list_object.server.execute_request.async_return_value = response
    with mock.patch('uuid.uuid4') as uuid4:
        uuid4.return_value = 'request#1'
        yield from proxy_list_object.fetch_elements('id', 9, 0, 100)
    proxy_list_object.server.execute_request.assert_called_with(
        Request(services.types.packet, test_iface, ['test-path'], 'fetch_elements', 'request#1',
                params=test_iface.get_command('fetch_elements').params_type('id', 9, 0, 100)))

    # elements fetched by first two calls must be merged together
    observer = mock.Mock(spec=ListObserver)
    proxy_list_object.subscribe(observer)
    proxy_list_object.server.reset_mock()
    chunk = yield from proxy_list_object.fetch_elements('id', None, 0, 100)
    assert chunk.bof
    assert not chunk.eof
    assert chunk.elements == [Element(i, test_iface.Row(i)) for i in range(20)]
    observer.process_fetch_result.assert_called_once_with(chunk)
    proxy_list_object.server.execute_request.assert_not_called()


def element(key):
    return Element(key, test_iface.Row(key), order_key=key)

@pytest.mark.parametrize('diff,expected_keys', [
    (ListDiff.add_one(element(4)), [0, 1, 2, 3, 4, 5, 6, 7]),
    (ListDiff.delete(2), [0, 1, 3, 5, 6, 7]),
    ])
@pytest.mark.asyncio
@asyncio.coroutine
def test_list_diff(proxy_list_object, diff, expected_keys):
    initial_keys = [0, 1, 2, 3, 5, 6, 7]

    # populate with initial elements
    fetch_result = test_iface.Contents(
        chunk=Chunk(
            sort_column_id='id',
            from_key=None,
            elements=[element(key) for key in initial_keys],
            bof=True,
            eof=False,
            ).to_data(test_iface))
    response = mock.Mock(error=None, result=fetch_result)
    proxy_list_object.server.execute_request.async_return_value = response
    yield from proxy_list_object.fetch_elements('id', None, 0, 100)

    proxy_list_object.process_diff(diff)

    proxy_list_object.server.reset_mock()
    chunk = yield from proxy_list_object.fetch_elements('id', None, 0, 100)
    assert chunk.bof
    assert not chunk.eof
    assert chunk.elements == [element(key) for key in expected_keys]
    proxy_list_object.server.execute_request.assert_not_called()
