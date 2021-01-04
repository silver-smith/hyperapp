from hyperapp.common.code_registry import CodeRegistry
from hyperapp.common.module import Module


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.identity_registry = CodeRegistry('identity', services.ref_resolver, services.types)
        services.peer_registry = CodeRegistry('peer', services.ref_resolver, services.types)
        services.signature_registry = CodeRegistry('signature', services.ref_resolver, services.types)
        services.parcel_registry = CodeRegistry('parcel', services.ref_resolver, services.types)
