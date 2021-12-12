from hyperapp.common.module import Module


class FactoryResource:

    @classmethod
    def from_dict(cls, data):
        return cls()

    def __init__(self):
        pass


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry['factory'] = FactoryResource.from_dict
