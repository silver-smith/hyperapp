import os.path
import asyncio
import logging
import time
from types import SimpleNamespace
import pytest
from PySide.QtTest import QTest
from hyperapp.common.htypes import tString, tInt, list_handle_type, Column
from hyperapp.common.services import ServicesBase
from hyperapp.client.async_application import AsyncApplication
from hyperapp.client.list_object import Element, Slice, ListObject
from hyperapp.client.list_view import View

log = logging.getLogger(__name__)


class ResourcesManager(object):

    def __init__(self, resources):
        self._resources = resources

    def resolve(self, resource_id):
        log.debug('resolving resource: %s', resource_id)
        return self._resources.get('.'.join(resource_id))


class Services(ServicesBase):

    def __init__(self):
        self.interface_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../common/interface'))
        ServicesBase.init_services(self)
        self._load_type_modules([
                'resource',
                'core',
                ])


class StubObject(ListObject):

    def get_columns(self):
        return [
            Column('key', type=tInt),
            Column('title'),
            ]

    def get_key_column_id(self):
        return 'key'

    @asyncio.coroutine
    def fetch_elements(self, sort_column_id, key, desc_count, asc_count):
        log.debug('StubObject.fetch_elements: sort_column_id=%s, key=%r, desc_count=%d, asc_count=%d', sort_column_id, key, desc_count, asc_count)
        assert sort_column_id == 'key'
        if key is None and desc_count == 0:
            elements = [Element(key, SimpleNamespace(key=key, title='title.%03d' % key)) for key in range(20)]
            slice = Slice(sort_column_id, 0, elements, bof=True, eof=True)
            self._notify_fetch_result(slice)
        else:
            assert 0


# not used directly but required to exist before creating gui objects
@pytest.fixture
def application():
    app = AsyncApplication()
    return app

@pytest.fixture
def event_loop(application):
    return application.event_loop
    
@pytest.fixture
def services():
    return Services()

@pytest.fixture
def list_view(application, services):
    resource_manager = ResourcesManager({
        })
    object = StubObject()
    data_type = list_handle_type(services.types.core, tString)
    return View(
        locale='en',
        parent=None,
        resources_manager=resource_manager,
        resource_id=['test', 'list'],
        data_type=data_type,
        object=object,
        key='key',
        sort_column_id='key',
        )

@pytest.mark.asyncio
@asyncio.coroutine
def test_list_view(list_view):
    list_view.show()
    #application.stop_loop()
    #application.exec_()
    #QTest.qWaitForWindowShown(list_view)
    #time.sleep(1)
    log.debug('done')
    assert 0  # just show me the logs
