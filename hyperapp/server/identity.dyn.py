from hyperapp.common.module import Module


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        # todo: store&load to/from file, remove fast=True.
        services.server_identity = services.generate_rsa_identity(fast=True)
