import os.path
import logging
import time
from collections import namedtuple
from itertools import chain
from operator import attrgetter
from pathlib import Path

import pytest
from PySide import QtCore, QtGui
from PySide.QtTest import QTest

from hyperapp.common.htypes import tInt, resource_key_t
from hyperapp.common.ref import phony_ref
from hyperapp.common import cdr_coders  # register codec
from hyperapp.client.services import ClientServicesBase
from hyperapp.client.list_object import Element, Chunk, ListDiff, Column, ListObject
from hyperapp.test.test_services import TestServicesMixin
from hyperapp.test.utils import resolve_type
from hyperapp.client.test.utils import wait_for_all_tasks_to_complete

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.client.test.fixtures']

DEFAULT_ROW_COUNT = 50
DEFAULT_ROWS_PER_FETCH = 10

HYPERAPP_DIR = Path(__file__).parent.parent.parent.resolve()


type_module_list = [
    'resource',
    'core',
    ]

code_module_list = [
    'common.resource_registry',
    'common.resource_resolver',
    'client.module_command_registry',
    'client.objimpl_registry',
    'client.view',
    'client.view_registry',
    'client.list_view',
    ]


class Services(ClientServicesBase, TestServicesMixin):

    def __init__(self):
        super().__init__()
        self.init_services()
        self.load_modules(type_module_list, code_module_list)


Row = namedtuple('Row', 'key title column_1 column_2')

def make_row(key):
    return Row(
        key=key,
        title='title.%03d' % key,
        column_1=(key % 10) * 10 + key//10,
        column_2=(key % 20) * 20 + key//20,
        )

def element(key):
    return Element(key, make_row(key))

def element_for_row(row):
    return Element(row.key, row)


class StubObject(ListObject):

    def __init__(self, rows_per_fetch=None, row_count=None, keys=None):
        ListObject.__init__(self)
        self._rows_per_fetch = rows_per_fetch or DEFAULT_ROWS_PER_FETCH
        self._rows = [make_row(key) for key in keys or list(range(row_count or DEFAULT_ROW_COUNT))]

    def get_columns(self):
        return [
            Column('key', type=tInt),
            Column('title'),
            Column('column_1', type=tInt),
            Column('column_2', type=tInt),
            ]

    def get_key_column_id(self):
        return 'key'

    async def fetch_elements_impl(self, sort_column_id, key, desc_count, asc_count):
        sorted_rows = sorted(self._rows, key=attrgetter(sort_column_id))
        log.debug('StubObject.fetch_elements: sort_column_id=%s key=%r desc_count=%d asc_count=%d sorted_rows=%r',
                  sort_column_id, key, desc_count, asc_count, [row.key for row in sorted_rows])
        key2idx = dict((row.key, idx) for idx, row in enumerate(sorted_rows))
        assert desc_count == 0, repr(desc_count)  # Not supported
        if key is not None:
            start = key2idx[key] + 1
        else:
            start = 0
        end = min(start + self._rows_per_fetch, len(sorted_rows))
        bof = start == 0
        eof = end == len(sorted_rows)
        elements = [element_for_row(row) for row in sorted_rows[start:end]]
        return Chunk(sort_column_id, key, elements, bof=bof, eof=eof)


@pytest.fixture
def event_loop(application):
    return application.event_loop


@pytest.fixture
def services():
    services = Services()
    services.start()
    yield services
    services.stop()


@pytest.fixture
def object():
    return StubObject()



@pytest.fixture
def locale():
    return 'en'


@pytest.fixture
def list_view_resource_key():
    return resource_key_t(phony_ref('test_list_view'), ['test-list'])


@pytest.fixture
def resource_registar(services, locale, list_view_resource_key):

    def register_resource(path, resource):
        resource_ref = services.ref_registry.register_object(resource)
        resource_key = resource_key_t(list_view_resource_key.module_ref, list_view_resource_key.path + path.split('.'))
        services.resource_registry.register(resource_key, locale, resource_ref)

    return register_resource


@pytest.fixture
def list_view_factory(application, services, object, locale, list_view_resource_key):
    default_object = object
    data_type = resolve_type(services, 'core', 'int_list_handle')
        
    def make_list_view(object=None, sort_column_id=None, current_key=None):
        return services.list_view_factory(
            locale=locale,
            parent=None,
            resource_key=list_view_resource_key,
            data_type=data_type,
            object=object or default_object,
            key=current_key,
            sort_column_id=sort_column_id or 'key',
            )

    return make_list_view


def get_cell(list_view, row, column):
    model = list_view.model()
    return model.data(model.createIndex(row, column), QtCore.Qt.DisplayRole)

def row_count_and_rows_per_fetch_and_key():
    for row_count in chain(range(1, 6), [10, 11, 15, 20, 50]):
        for rows_per_fetch in chain(range(1, 10), range(10, row_count + 1, 10)):
            for current_key in [0, 1, 2, 5, 10, 20, row_count - 1]:
                if rows_per_fetch > row_count: continue
                if current_key >= row_count: continue
                values = (row_count, rows_per_fetch, current_key)
                if values != (50, 2, 20):
                    values = pytest.param(*values, marks=pytest.mark.slow)
                yield values

def get_list_view_row_count(list_view):
    return list_view.model().rowCount(QtCore.QModelIndex())

def check_rows(list_view, sort_column_id, expected_row_count):
    sort_column_idx = Row._fields.index(sort_column_id)
    assert get_list_view_row_count(list_view) >= expected_row_count
    for row in range(0, expected_row_count):
        key = int(get_cell(list_view, row, 0))
        assert get_cell(list_view, row, 1) == str(make_row(key).title)
        assert get_cell(list_view, row, 2) == str(make_row(key).column_1)
        assert get_cell(list_view, row, 3) == str(make_row(key).column_2)
        if row > 0:
            assert (int(get_cell(list_view, row - 1, sort_column_idx)) <=
                    int(get_cell(list_view, row, sort_column_idx)))

@pytest.mark.asyncio
@pytest.mark.parametrize('row_count,rows_per_fetch,current_key', row_count_and_rows_per_fetch_and_key())
async def test_rows_fetched_and_current_key_set(list_view_factory, row_count, rows_per_fetch, current_key):
    object = StubObject(rows_per_fetch, row_count)
    list_view = list_view_factory(object, current_key=current_key)
    #list_view.show()
    list_view.fetch_elements_if_required()  # normally called from resizeEvent when view is shown
    #application.stop_loop()
    #application.exec_()
    #QTest.qWaitForWindowShown(list_view)
    first_visible_row, visible_row_count = list_view._get_visible_rows()
    model = list_view.model()
    await wait_for_all_tasks_to_complete()
    expected_row_count = min(row_count, visible_row_count)
    assert model.columnCount(QtCore.QModelIndex()) == 4
    check_rows(list_view, 'key', expected_row_count)
    for row in range(expected_row_count):
        assert get_cell(list_view, row, 0) == str(make_row(row).key)
    assert list_view.get_current_key() == current_key
    # without resource column_id is used for header
    assert model.headerData(1, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.DisplayRole) == 'title'

@pytest.mark.asyncio
async def test_overlapped_fetch_result_should_be_merged_properly(list_view_factory):
    row_count = 10
    object = StubObject(rows_per_fetch=10, row_count=row_count)
    list_view = list_view_factory(object)
    list_view.fetch_elements_if_required()  # normally called from resizeEvent when view is shown
    first_visible_row, visible_row_count = list_view._get_visible_rows()
    model = list_view.model()
    await wait_for_all_tasks_to_complete()
    expected_row_count = min(row_count, visible_row_count)
    actual_row_count = get_list_view_row_count(list_view)
    check_rows(list_view, 'key', expected_row_count)
    rows = [make_row(key) for key in range(row_count)]
    elements = [element_for_row(row) for row in rows]
    chunk = Chunk(sort_column_id='key', from_key=None, elements=elements, bof=True, eof=True)
    object._notify_fetch_result(chunk)
    assert get_list_view_row_count(list_view) == actual_row_count  # no new rows are expected
    check_rows(list_view, 'key', actual_row_count)

@pytest.mark.asyncio
async def test_resources_used_for_header_and_visibility(services, resource_registar, list_view_factory):
    column_resource = resolve_type(services, 'resource', 'column_resource')
    resource_registar('column.key', column_resource(is_visible=False, text='the key', description=''))
    resource_registar('column.title', column_resource(is_visible=True, text='the title', description=''))
    list_view = list_view_factory()
    list_view.fetch_elements_if_required()  # called from resizeEvent when view is shown
    first_visible_row, visible_row_count = list_view._get_visible_rows()
    model = list_view.model()
    await wait_for_all_tasks_to_complete()
    assert model.columnCount(QtCore.QModelIndex()) == 3  # key column must be hidden
    assert model.headerData(0, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.DisplayRole) == 'the title'

@pytest.mark.parametrize('diff,expected_keys', [
    (ListDiff.add_one(element(4)), [0, 1, 2, 3, 4, 5, 6, 7]),
    (ListDiff.add_many([element(8), element(9)]), [0, 1, 2, 3, 5, 6, 7, 8, 9]),
    (ListDiff.delete(2), [0, 1, 3, 5, 6, 7]),
    ])
@pytest.mark.asyncio
async def test_diff(list_view_factory, diff, expected_keys):
    keys = [0, 1, 2, 3, 5, 6, 7]
    object = StubObject(keys=keys)
    current_key = keys[-1]  # last key to force loading all rows
    list_view = list_view_factory(object, current_key=current_key)
    list_view.fetch_elements_if_required()  # normally called from resizeEvent when view is shown
    model = list_view.model()
    await wait_for_all_tasks_to_complete()
    list_view.diff_applied(diff)
    await wait_for_all_tasks_to_complete()
    check_rows(list_view, sort_column_id='key', expected_row_count=len(expected_keys))
    for row, key in enumerate(expected_keys):
        assert get_cell(list_view, row, 0) == str(key)
    # assert list_view.get_current_key() == current_key  # must not change; todo

@pytest.mark.parametrize('sort_column_id', ['column_1', 'column_2'])
@pytest.mark.parametrize('row_count,rows_per_fetch,current_key', row_count_and_rows_per_fetch_and_key())
@pytest.mark.asyncio
async def test_sort_by_non_key_column(list_view_factory, sort_column_id, row_count, rows_per_fetch, current_key):
    sort_column_idx = Row._fields.index(sort_column_id)
    object = StubObject(rows_per_fetch, row_count)
    list_view = list_view_factory(object, sort_column_id=sort_column_id, current_key=current_key)
    list_view.fetch_elements_if_required()  # normally called from resizeEvent when view is shown
    first_visible_row, visible_row_count = list_view._get_visible_rows()
    model = list_view.model()
    await wait_for_all_tasks_to_complete()
    expected_row_count = min(row_count, visible_row_count)
    assert model.columnCount(QtCore.QModelIndex()) == 4
    check_rows(list_view, sort_column_id, expected_row_count)
    assert list_view.get_current_key() == current_key
