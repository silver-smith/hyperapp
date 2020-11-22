import pytest

from hyperapp.common.services import ServicesBase


class Services(ServicesBase):

    def schedule_stopping(self):
        self.stop()


@pytest.fixture
def type_module_list():
    return []


@pytest.fixture
def code_module_list():
    return []


@pytest.fixture
def services(type_module_list, code_module_list):
    services = Services()
    services.init_services()
    services.init_modules(type_module_list, code_module_list)
    services.start()
    yield services
    services.stop()
