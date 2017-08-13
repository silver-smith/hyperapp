import os.path
import asyncio
import logging
import time
from types import SimpleNamespace
import pytest
from PySide import QtCore, QtGui
from PySide.QtTest import QTest
from hyperapp.common.htypes import tString, tInt, list_handle_type, Column
from hyperapp.common.services import ServicesBase
from hyperapp.client.async_application import AsyncApplication
from hyperapp.client.list_object import Element, Slice, ListObject
from hyperapp.client.list_view import View

log = logging.getLogger(__name__)


ROW_COUNT = 20


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

    def __init__(self, rows_per_fetch):
        ListObject.__init__(self)
        self._rows_per_fetch = rows_per_fetch

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
        if desc_count == 0:
            if key is not None:
                start = key + 1
                bof = False
            else:
                start = 0
                bof = True
            end = start + self._rows_per_fetch
            if end >= ROW_COUNT:
                end = ROW_COUNT
                eof = True
            else:
                eof = False
            elements = [Element(key, SimpleNamespace(key=key, title='title.%03d' % key)) for key in range(start, end)]
            slice = Slice(sort_column_id, 0, elements, bof=bof, eof=eof)
            self._notify_fetch_result(slice)
        else:
            assert 0


# required to exist when creating gui objects
@pytest.fixture(scope='module')
def application():
    return AsyncApplication()

@pytest.fixture
def event_loop(application):
    return application.event_loop
    
@pytest.fixture
def services():
    return Services()

@pytest.fixture(params=range(1, 10))
def object(request):
    return StubObject(rows_per_fetch=request.param)

@pytest.fixture
def list_view(application, services, object):
    resource_manager = ResourcesManager({
        })
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

@asyncio.coroutine
def wait_for(timeout_sec, fn, *args, **kw):
    t = time.time()
    while not fn(*args, **kw):
        if time.time() - t > timeout_sec:
            assert False, 'Timed out in %s seconds' % timeout_sec
        yield from asyncio.sleep(0.1)

@pytest.mark.asyncio
@asyncio.coroutine
def test_list_view(list_view):
    #list_view.show()
    list_view.fetch_elements_if_required()  # called from resizeEvent when view is shown
    #application.stop_loop()
    #application.exec_()
    #QTest.qWaitForWindowShown(list_view)
    #time.sleep(1)
    model = list_view.model()
    yield from wait_for(1, lambda: model.columnCount(QtCore.QModelIndex()) == 2)
    yield from wait_for(1, lambda: model.rowCount(QtCore.QModelIndex()) == ROW_COUNT)
    for row in range(ROW_COUNT):
        assert model.data(model.createIndex(row, 0), QtCore.Qt.DisplayRole) == str(row)
        assert model.data(model.createIndex(row, 1), QtCore.Qt.DisplayRole) == 'title.%03d' % row
    log.debug('done')
    # assert 0  # just show me the logs
