from hyperapp.common.module import Module


class FactoryResource:

    @classmethod
    def from_dict(cls, data, name_to_resource):
        object = name_to_resource[data['object']]
        params = {
            name: name_to_resource[resource_name]
            for name, resource_name
            in data['params'].items()
            }
        return cls(object, params)

    def __init__(self, object, params):
        self._object = object
        self._params = params

    def __repr__(self):
        return f"<FactoryResource: {self._object}({self._params})>"


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry['factory'] = FactoryResource.from_dict
