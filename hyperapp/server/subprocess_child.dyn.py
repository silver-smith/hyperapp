from hyperapp.common.module import Module


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.master_process_route = SubprocessRoute(services.ref_registry, services.ref_collector_factory, connection)
