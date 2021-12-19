from hyperapp.common.module import Module

from . import htypes


class CallResource:

    def __init__(self, function):
        self._function = function

    def __repr__(self):
        return f"<CallResource: {self._function}>"

    def value(self):
        fn = self._function.value()
        return fn()



def from_dict(data, name_to_resource):
    fn_object_ref = name_to_resource[data['function']]
    return htypes.call.call(fn_object_ref)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry['call'] = from_dict
