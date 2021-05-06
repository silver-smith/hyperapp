from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module import Module


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.identity_registry = CodeRegistry('identity', services.web, services.types)
        services.peer_registry = CodeRegistry('peer', services.web, services.types)
        services.signature_registry = CodeRegistry('signature', services.web, services.types)
        services.parcel_registry = CodeRegistry('parcel', services.web, services.types)
