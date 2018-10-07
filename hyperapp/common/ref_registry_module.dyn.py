# registry for transient references

from .ref_registry import RefRegistry
from .module import Module


MODULE_NAME = 'ref_registry'


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.ref_registry = ref_registry = RefRegistry(services.types)
        services.ref_resolver.add_source(ref_registry)
