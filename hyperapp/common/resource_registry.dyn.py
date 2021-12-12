import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ResourceRegistry:

    def __init__(self, resource_type_registry, builtin_resource_by_name):
        self._resource_type_registry = resource_type_registry
        self._builtin_resource_by_name = builtin_resource_by_name

    def load_definitions(self, resources):
        name_to_resource = {**self._builtin_resource_by_name}
        for name, definition in resources.items():
            from_dict = self._resource_type_registry[definition['type']]
            resource = from_dict(definition, name_to_resource)
            name_to_resource[name] = resource
            log.info("Loaded resource %r: %s", name, resource)
        return name_to_resource


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_registry = {}  # resource name -> from_dict constructor.
        services.builtin_resource_by_name = {}
        services.resource_registry = ResourceRegistry(services.resource_type_registry, services.builtin_resource_by_name)
