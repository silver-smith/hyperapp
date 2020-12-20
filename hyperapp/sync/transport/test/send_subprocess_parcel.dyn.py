from hyperapp.common.htypes import ref_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

from .rsa_identity import RsaIdentity


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        master_peer_ref = packet_coders.decode('cdr', config['master_peer_ref_cdr'], ref_t)
        my_identity = RsaIdentity.generate(fast=True)
        services.transport.send(None)
