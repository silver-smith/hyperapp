from functools import partial

from hyperapp.common.module import Module

from . import htypes


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_reg['list_service'] = services.resource_type_factory(htypes.resource_service.list_service)
