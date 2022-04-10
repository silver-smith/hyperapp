from hyperapp.common.module import Module


class MockFileBundle:

    def __init__(self, path, encoding=None):
        pass

    def load_ref(self):
        raise FileNotFoundError("Mock file bundle")

    def load_piece(self):
        raise FileNotFoundError("Mock file bundle")


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.file_bundle = MockFileBundle
