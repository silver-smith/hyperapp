from functools import partial

from hyperapp.common.module import Module


class FactoryResource:

    @classmethod
    def from_dict(cls, data, name_to_resource):
        object = name_to_resource[data['object']]
        attr_name = data['attr_name']
        params = {
            name: name_to_resource[resource_name]
            for name, resource_name
            in data.get('params', {}).items()
            }
        return cls(object, attr_name, params)

    def __init__(self, object, attr_name, params):
        self._object = object
        self._attr_name = attr_name
        self._params = params

    def __repr__(self):
        return f"<FactoryResource: {self._object}.{self._attr_name}({self._params})>"

    def value(self):
        kw = {
            name: resource.value()
            for name, resource
            in self._params.items()
            }
        object = self._object.value()
        fn = getattr(object, self._attr_name)
        if kw:
            return partial(fn, **kw)
        else:
            return fn


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry['factory'] = FactoryResource.from_dict
