from collections import namedtuple
import logging
from pathlib import Path

import pytest

from hyperapp.common.htypes import tInt, resource_key_t
from hyperapp.common.ref import phony_ref
from hyperapp.client.services import ClientServicesBase
from hyperapp.test.test_services import TestServicesMixin
from hyperapp.client.test.utils import wait_for_all_tasks_to_complete

log = logging.getLogger(__name__)


pytest_plugins = ['hyperapp.client.test.fixtures']

HYPERAPP_DIR = Path(__file__).parent.parent.parent.resolve()


type_module_list = [
    'resource',
    'core',
    'tree_view',
    ]

code_module_list = [
    'common.resource_registry',
    'common.resource_resolver',
    'client.module_command_registry',
    'client.objimpl_registry',
    'client.view',
    'client.view_registry',
    'client.column',
    'client.tree_object',
    'client.tree_view',
    ]


class Services(ClientServicesBase, TestServicesMixin):

    def __init__(self):
        super().__init__()
        self.init_services()
        self.load_modules(type_module_list, code_module_list)


Item = namedtuple('Item', 'name column_1 column_2')


@pytest.fixture(autouse=True)
def event_loop(application):
    return application.event_loop


@pytest.fixture
def services():
    services = Services()
    services.start()
    yield services
    services.stop()


@pytest.fixture
def object(services):

    class StubObject(services.TreeObject):

        def get_columns(self):
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
async def test_instantiate(services, object):
    view = services.tree_view_factory(
        columns=[column.to_view_column(column.id) for column in object.get_columns()],
        object=object,
        current_path=None,
        )
    #view.populate()
    await wait_for_all_tasks_to_complete()
