import pytest

from hyperapp.common.services import ServicesBase


class Services(ServicesBase):

    def load_modules(self, type_module_list, code_module_list):
        try:
            self._load_type_module_list(type_module_list)
            self._load_code_module_list(code_module_list)
        finally:
            self.code_module_importer.unregister_meta_hook()

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
    services.load_modules(type_module_list, code_module_list)
    services.module_registry.init_phases(services)
    services.start()
    yield services
    services.stop()
