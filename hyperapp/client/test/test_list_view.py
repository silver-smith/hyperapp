import os.path
import asyncio
import pytest
from PySide.QtGui import QApplication
from hyperapp.common.htypes import tString, list_handle_type, Column
from hyperapp.common.services import ServicesBase
from hyperapp.client.list_object import ListObject
from hyperapp.client.list_view import View


class ResourcesManager(object):

    def __init__(self, resources):
        self._resources = resources

    def resolve(self, resource_id):
        print('resolving resource:', resource_id)
        return self._resources.get('.'.join(resource_id))


class Services(ServicesBase):

    def __init__(self):
        self.interface_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../common/interface'))
        ServicesBase.init_services(self)
        self._load_type_modules([
                'resource',
                'core',
                ])


class TestObject(ListObject):

    def get_columns(self):
        return [
            Column('key'),
            Column('title'),
            ]

    def get_key_column_id(self):
        return 'key'

    @asyncio.coroutine
    def fetch_elements(self, sort_column_id, key, desc_count, asc_count):
        pass


@pytest.fixture
def application():
    return QApplication([])

@pytest.fixture
def services():
    return Services()

@pytest.fixture
def list_view(application, services):
    resource_manager = ResourcesManager({
        })
    object = TestObject()
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

def test_list_view(list_view):
    pass
