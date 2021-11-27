import asyncio
import logging
from collections import namedtuple
from pathlib import Path

import pytest

from hyperapp.common.htypes import tInt
from hyperapp.common.services import Services
from hyperapp.client.test.utils import wait_for_all_tasks_to_complete
from hyperapp.common import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.common.test.services']


@pytest.fixture
def code_module_list():
    return  [
        'common.layered_config_sheet',
        'async.ui.qt.application',  # Use Qt event loop.
        'async.ui.tree_object',
        'async.ui.qt.tree_view',
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
async def test_instantiate(event_loop, services, code, object):
    view = code.tree_view.TreeView(object=object)
    #view.populate()
    await wait_for_all_tasks_to_complete(event_loop)
