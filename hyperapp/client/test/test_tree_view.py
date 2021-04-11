import asyncio
import logging
from collections import namedtuple
from pathlib import Path

import pytest

from hyperapp.common.htypes import tInt, resource_key_t
from hyperapp.common.services import Services
from hyperapp.client.test.utils import wait_for_all_tasks_to_complete
from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def type_module_list():
    return [
        'layout',
        'object_type',
        'object_layout_association',
        'tree_object',
        'line',
        'record_object',
        'tree_view',
        'params_editor',
        ]

@pytest.fixture
def code_module_list():
    return  [
        'common.resource_registry',
        'common.resource_resolver',
        'common.weak_key_dictionary_with_callback',
        'async.ui.commander',
        'async.ui.object',
        'async.ui.module',
        'client.module_command_registry',
        'async.async_web',
        'async.async_registry',
        'async.code_registry',
        'client.object_registry',
        'client.view_registry',
        'client.object_layout_association',
        'async.ui.qt.util',
        'async.ui.qt.qt_keys',
        'async.ui.qt.application',
        'client.view',
        'client.items_view',
        'client.layout_handle',
        'client.layout_command',
        'client.self_command',
        'client.layout',
        'client.record_object',
        'client.chooser',
        'client.params_editor',
        'client.items_view',
        'client.column',
        'client.tree_object',
        'client.tree_view',
        ]


Item = namedtuple('Item', 'name column_1 column_2')


@pytest.fixture
def event_loop(services):
    loop = services.event_loop_ctr()
    yield loop
    services.event_loop_dtr()
    # Next pytest_asyncio test fails complaining event loop is running.
    # Possibly, that is related to pytest_asyncio specifics.
    # This hack helps:
    asyncio._set_running_loop(None)


@pytest.fixture
def object(services):

    class StubObject(services.TreeObject):

        @property
        def piece(self):
            raise NotImplementedError()

        @property
        def title(self):
            raise NotImplementedError()

        @property
        def columns(self):
            return [
                services.Column('name', is_key=True),
                services.Column('column_1', type=tInt),
                services.Column('column_2', type=tInt),
                ]

        async def fetch_items(self, path):
            self._distribute_fetch_results(path, [
                Item('item-%d' % idx, 'column 1 for #%d' % idx, 'column 2 for #%d' % idx)
                for idx in range(10)])


    return StubObject()


@pytest.mark.asyncio
async def test_instantiate(event_loop, services, object):
    view = services.tree_view_factory(
        columns=[column.to_view_column(column.id) for column in object.columns],
        object=object,
        current_path=None,
        )
    #view.populate()
    await wait_for_all_tasks_to_complete(event_loop)
