from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module import Module


class ThisModule(Module):

    def __init__(self, module_name, services):
        super().__init__(module_name)
        services.identity_registry = CodeRegistry('identity', services.ref_resolver, services.types)
