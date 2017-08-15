import os.path
import asyncio
import logging
import time
from types import SimpleNamespace
from itertools import chain
import pytest
from PySide import QtCore, QtGui
from PySide.QtTest import QTest
from hyperapp.common.htypes import tString, tInt, list_handle_type, Column
from hyperapp.common.services import ServicesBase
from hyperapp.client.async_application import AsyncApplication
from hyperapp.client.list_object import ListDiff, Element, Slice, ListObject
from hyperapp.client.list_view import View

log = logging.getLogger(__name__)


DEFAULT_ROW_COUNT = 50
DEFAULT_ROWS_PER_FETCH = 10


class ResourcesManager(object):

    def __init__(self, resources=None):
        self._resources = resources or {}

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


def element(key):
    return Element(key, SimpleNamespace(key=key, title='title.%03d' % key))


class StubObject(ListObject):

    def __init__(self, rows_per_fetch=None, row_count=None, keys=None):
        ListObject.__init__(self)
        self._rows_per_fetch = rows_per_fetch or DEFAULT_ROWS_PER_FETCH
        self._keys = keys or list(range(row_count or DEFAULT_ROW_COUNT))

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
                start = self._keys.index(key) + 1
                bof = False
            else:
                start = 0
                bof = True
            end = start + self._rows_per_fetch
            if end >= len(self._keys):
                end = len(self._keys)
                eof = True
            else:
                eof = False
            elements = [element(self._keys[row]) for row in range(start, end)]
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

@pytest.fixture
def object():
    return StubObject()

@pytest.fixture
def list_view_factory(application, services, object):
    default_object = object
    data_type = list_handle_type(services.types.core, tInt)

    def make_list_view(object=None, key=None, resources=None):
        resource_manager = ResourcesManager(resources)
        return View(
            locale='en',
            parent=None,
            resources_manager=resource_manager,
            resource_id=['test', 'list'],
            data_type=data_type,
            object=object or default_object,
            key=key,
            sort_column_id='key',
            )

    return make_list_view

@asyncio.coroutine
def wait_for(timeout_sec, fn, *args, **kw):
    t = time.time()
    while not fn(*args, **kw):
        if time.time() - t > timeout_sec:
            assert False, 'Timed out in %s seconds' % timeout_sec
        yield from asyncio.sleep(0.1)

@asyncio.coroutine
def wait_for_all_tasks_to_complete(timeout_sec=1):
    t = time.time()
    future = asyncio.Future()
    def check_pending():
        pending = [task for task in asyncio.Task.all_tasks() if not task.done()]
        log.debug('%d pending tasks:', len(pending))
        for task in pending:
            log.debug('\t%s', task)
        if len(pending) > 1:  # only test itself must be left
            if time.time() - t > timeout_sec:
                future.set_exception(RuntimeError('Timed out waiting for all tasks to complete in %s seconds' % timeout_sec))
            else:
                asyncio.get_event_loop().call_soon(check_pending)
        else:
            future.set_result(None)
    asyncio.get_event_loop().call_soon(check_pending)
    yield from future


def row_count_and_rows_per_fetch_and_key():
    for row_count in chain(range(1, 6), [10, 11, 15, 20, 50]):
        for rows_per_fetch in chain(range(1, 10), range(10, row_count + 1, 10)):
            for key in [0, 1, 2, 5, 10, 20, row_count - 1]:
                if rows_per_fetch > row_count: continue
                if key >= row_count: continue
                values = (row_count, rows_per_fetch, key)
                if values != (50, 2, 20):
                    values = pytest.param(*values, marks=pytest.mark.slow)
                yield values

@pytest.mark.asyncio
@pytest.mark.parametrize('row_count,rows_per_fetch,key', row_count_and_rows_per_fetch_and_key())
@asyncio.coroutine
def test_rows_fetched_and_current_key_set(list_view_factory, row_count, rows_per_fetch, key):
    object = StubObject(rows_per_fetch, row_count)
    list_view = list_view_factory(object, key)
    #list_view.show()
    list_view.fetch_elements_if_required()  # normally called from resizeEvent when view is shown
    #application.stop_loop()
    #application.exec_()
    #QTest.qWaitForWindowShown(list_view)
    first_visible_row, visible_row_count = list_view._get_visible_rows()
    model = list_view.model()
    yield from wait_for_all_tasks_to_complete()
    expected_row_count = min(row_count, visible_row_count)
    assert model.columnCount(QtCore.QModelIndex()) == 2
    assert model.rowCount(QtCore.QModelIndex()) >= expected_row_count
    for row in range(expected_row_count):
        assert model.data(model.createIndex(row, 0), QtCore.Qt.DisplayRole) == str(row)
        assert model.data(model.createIndex(row, 1), QtCore.Qt.DisplayRole) == 'title.%03d' % row
    assert list_view.get_current_key() == key
    # without resource column_id is used for header
    assert model.headerData(1, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.DisplayRole) == 'title'

@pytest.mark.asyncio
@asyncio.coroutine
def test_resources_used_for_header_and_visibility(services, list_view_factory):
    resources = {
        'test.list.column.key.en': services.types.resource.column_resource(visible=False, text='the key', description=''),
        'test.list.column.title.en': services.types.resource.column_resource(visible=True, text='the title', description=''),
        }
    list_view = list_view_factory(resources=resources)
    list_view.fetch_elements_if_required()  # called from resizeEvent when view is shown
    first_visible_row, visible_row_count = list_view._get_visible_rows()
    model = list_view.model()
    yield from wait_for_all_tasks_to_complete()
    assert model.columnCount(QtCore.QModelIndex()) == 1  # key column must be hidden
    assert model.headerData(0, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.DisplayRole) == 'the title'

@pytest.mark.asyncio
@asyncio.coroutine
def test_diff(services, list_view_factory):
    keys = [0, 1, 2, 3, 5, 6, 7]
    object = StubObject(keys=keys)
    current_key = keys[-1]  # last key to force loading all rows
    list_view = list_view_factory(object, key=current_key)
    list_view.fetch_elements_if_required()  # normally called from resizeEvent when view is shown
    model = list_view.model()

    @asyncio.coroutine
    def assert_keys(expected_keys):
        yield from wait_for_all_tasks_to_complete()
        assert model.rowCount(QtCore.QModelIndex()) == len(expected_keys)
        for row, key in enumerate(expected_keys):
            assert model.data(model.createIndex(row, 0), QtCore.Qt.DisplayRole) == str(key)
            assert model.data(model.createIndex(row, 1), QtCore.Qt.DisplayRole) == 'title.%03d' % key
        # assert list_view.get_current_key() == current_key  # must not change; todo

    yield from assert_keys(keys)

    list_view.diff_applied(ListDiff.add_one(4, element(4)))
    yield from assert_keys([0, 1, 2, 3, 4, 5, 6, 7])

    list_view.diff_applied(ListDiff.append_many([element(8), element(9)]))
    yield from assert_keys([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

    list_view.diff_applied(ListDiff.delete(2))
    yield from assert_keys([0, 1, 3, 4, 5, 6, 7, 8, 9])
