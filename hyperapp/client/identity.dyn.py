from hyperapp.common.module import Module


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        # todo: make identity list, current identity; store in a file.
        services.client_identity = services.generate_rsa_identity(fast=True)
