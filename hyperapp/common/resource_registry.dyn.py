from hyperapp.common.module import Module



class ResourceRegistry:

    def __init__(self):
        pass


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_registry = ResourceRegistry()
        services.resource_type_registry = {}  # resource name -> from_dict constructor.
