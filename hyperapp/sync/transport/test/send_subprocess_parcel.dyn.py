from hyperapp.common.module import Module

from .rsa_identity import RsaIdentity


class ThisModule(Module):

    def __init__(self, module_name, services):
        super().__init__(module_name)
        my_identity = RsaIdentity.generate(fast=True)
        services.transport.send(None)
