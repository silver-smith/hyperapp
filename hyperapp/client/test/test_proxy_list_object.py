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
from hyperapp.common.list_object import Element, Slice, ListDiff
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

@pytest.fixture
def proxy_list_object(services, server):
    cache_repository = mock.Mock()
    cache_repository.load_value.return_value = []
    resources_manager = mock.Mock()
    resources_manager.resove.return_value = None
    param_editor_registry = mock.Mock()
    iface = ListInterface('test_iface', columns=[Column('id', type=tInt, is_key=True)])
    iface.register_types(services.types.core)
    return ProxyListObject(
        services.types.packet,
        services.types.core,
        services.iface_registry,
        cache_repository,
        resources_manager,
        param_editor_registry,
        server,
        ['test-path'],
        iface,
        )


@pytest.mark.asyncio
@asyncio.coroutine
def test_fetch_elements(proxy_list_object):
    iface = proxy_list_object.iface
    elements = [Element(i, iface.Row(i)) for i in range(10)]
    fetch_result = iface.Contents(
        slice=Slice(
            sort_column_id='id',
            from_key=None,
            elements=elements,
            bof=True,
            eof=True,
            ).to_data(iface))
    response = mock.Mock(error=None, result=fetch_result)
    proxy_list_object.server.execute_request.async_return_value = response
    observer = mock.Mock(spec=ListObserver)
    proxy_list_object.subscribe(observer)
    slice = yield from proxy_list_object.fetch_elements('id', None, 0, 100)
    assert slice.bof
    assert slice.eof
    assert slice.elements == elements
    observer.process_fetch_result.assert_called_once_with(slice)


@pytest.mark.asyncio
@asyncio.coroutine
def test_fetch_cached_elements(proxy_list_object):
    iface = proxy_list_object.iface
    elements = [Element(i, iface.Row(i)) for i in range(10)]
    fetch_result = iface.Contents(
        slice=Slice(
            sort_column_id='id',
            from_key=None,
            elements=elements,
            bof=True,
            eof=True,
            ).to_data(iface))
    response = mock.Mock(error=None, result=fetch_result)
    proxy_list_object.server.execute_request.async_return_value = response
    yield from proxy_list_object.fetch_elements('id', None, 0, 100)
    observer = mock.Mock(spec=ListObserver)
    proxy_list_object.subscribe(observer)
    proxy_list_object.server.reset_mock()
    # second call must fetch results from cache, server must not be called
    slice = yield from proxy_list_object.fetch_elements('id', None, 0, 10)
    assert slice.bof
    assert slice.eof
    assert slice.elements == elements
    observer.process_fetch_result.assert_called_once_with(slice)
    proxy_list_object.server.execute_request.assert_not_called()


# two adjacent slices must be merged when fetch results are processed
@pytest.mark.asyncio
@asyncio.coroutine
def test_slices_are_merged(services, proxy_list_object):
    iface = proxy_list_object.iface

    # fetch first 10 elements
    fetch_result = iface.Contents(
        slice=Slice(
            sort_column_id='id',
            from_key=None,
            elements=[Element(i, iface.Row(i)) for i in range(10)],
            bof=True,
            eof=False,
            ).to_data(iface))
    response = mock.Mock(error=None, result=fetch_result)
    proxy_list_object.server.execute_request.async_return_value = response
    yield from proxy_list_object.fetch_elements('id', None, 0, 100)

    # fetch next 10 elements
    fetch_result = iface.Contents(
        slice=Slice(
            sort_column_id='id',
            from_key=9,
            elements=[Element(i, iface.Row(i)) for i in range(10, 20)],
            bof=False,
            eof=False,
            ).to_data(iface))
    response = mock.Mock(error=None, result=fetch_result)
    proxy_list_object.server.execute_request.async_return_value = response
    with mock.patch('uuid.uuid4') as uuid4:
        uuid4.return_value = 'request#1'
        yield from proxy_list_object.fetch_elements('id', 9, 0, 100)
    proxy_list_object.server.execute_request.assert_called_with(
        Request(services.types.packet, iface, ['test-path'], 'fetch_elements', 'request#1',
                params=iface.get_command('fetch_elements').params_type('id', 9, 0, 100)))

    # elements fetched by first two calls must be merged together
    observer = mock.Mock(spec=ListObserver)
    proxy_list_object.subscribe(observer)
    proxy_list_object.server.reset_mock()
    slice = yield from proxy_list_object.fetch_elements('id', None, 0, 100)
    assert slice.bof
    assert not slice.eof
    assert slice.elements == [Element(i, iface.Row(i)) for i in range(20)]
    observer.process_fetch_result.assert_called_once_with(slice)
    proxy_list_object.server.execute_request.assert_not_called()


@pytest.mark.asyncio
@asyncio.coroutine
def test_list_diff(proxy_list_object):
    iface = proxy_list_object.iface

    # populate with 10 elements
    fetch_result = iface.Contents(
        slice=Slice(
            sort_column_id='id',
            from_key=None,
            elements=[Element(i, iface.Row(i)) for i in chain(range(0, 10), range(20, 30))],
            bof=True,
            eof=False,
            ).to_data(iface))
    response = mock.Mock(error=None, result=fetch_result)
    proxy_list_object.server.execute_request.async_return_value = response
    yield from proxy_list_object.fetch_elements('id', None, 0, 100)

    diff = ListDiff(remove_keys=[5, 7],
                    insert_before_key=None,
                    elements=[Element(i, iface.Row(i)) for i in range(10, 20)])
    proxy_list_object.process_diff(diff)

    # elements fetched by first two calls must be merged together
    proxy_list_object.server.reset_mock()
    slice = yield from proxy_list_object.fetch_elements('id', None, 0, 100)
    assert slice.bof
    assert not slice.eof
    assert slice.elements == [Element(i, iface.Row(i)) for i in range(30) if not i in [5, 7]]
    proxy_list_object.server.execute_request.assert_not_called()
