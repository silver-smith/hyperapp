from hyperapp.server.services import ServerServicesBase
from hyperapp.client.services import ClientServicesBase


class TestServicesMixin(object):

    __test__ = False

    def load_modules(self, type_module_list, code_module_list):
        try:
            self._load_type_module_list(type_module_list)
            self._load_code_module_list(code_module_list)
        finally:
            self.code_module_importer.unregister_meta_hook()


class TestServerServices(ServerServicesBase, TestServicesMixin):

    def __init__(self, type_module_list, code_module_list, config=None):
        super().__init__()
        self.init_services(config)
        self.load_modules(type_module_list, code_module_list)
        self.module_registry.init_phases(self)


class TestClientServices(ClientServicesBase, TestServicesMixin):

    def __init__(self, event_loop, type_module_list, code_module_list):
        super().__init__()
        self.event_loop = event_loop
        self.init_services()
        self.load_modules(type_module_list, code_module_list)
