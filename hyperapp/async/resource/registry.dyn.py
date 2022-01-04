
from hyperapp.common.module import Module

from .cached_async_code_registry import CachedAsyncCodeRegistry


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.python_object_acreg = CachedAsyncCodeRegistry('async_python_object', services.async_web, services.types)
