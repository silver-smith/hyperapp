from hyperapp.client.module import ClientModule

from .code_registry import CodeRegistry


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry = CodeRegistry('object', services.async_ref_resolver, services.type_resolver)
