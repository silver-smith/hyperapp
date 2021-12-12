from hyperapp.common.module import Module


class CallResource:

    @classmethod
    def from_dict(cls, data, name_to_resource):
        function = name_to_resource[data['function']]
        return cls(function)

    def __init__(self, function):
        self._function = function

    def __repr__(self):
        return f"<CallResource: {self._function}>"

    def value(self):
        fn = self._function.value()
        return fn()


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry['call'] = CallResource.from_dict
