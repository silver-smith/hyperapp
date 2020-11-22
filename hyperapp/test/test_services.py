from hyperapp.server.services import ServerServicesBase
from hyperapp.client.services import ClientServicesBase


class TestServerServices(ServerServicesBase):

    __test__ = False

    def __init__(self, type_module_list, code_module_list, config=None):
        super().__init__()
        self.init_services(config)
        self.init_modules(type_module_list, code_module_list)


class TestClientServices(ClientServicesBase):

    __test__ = False

    def __init__(self, event_loop, type_module_list, code_module_list):
        super().__init__(event_loop)
        self.init_services()
        self.init_modules(type_module_list, code_module_list)
