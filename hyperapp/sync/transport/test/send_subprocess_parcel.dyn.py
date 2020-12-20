from hyperapp.common.htypes import bundle_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

from .rsa_identity import RsaIdentity


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        master_peer_bundle = packet_coders.decode('cdr', config['master_peer_bundle_cdr'], bundle_t)
        master_peer_ref = master_peer_bundle.roots[0]
        services.unbundler.register_bundle(master_peer_bundle)
        master_peer = services.peer_registry.invite(master_peer_ref)
        my_identity = RsaIdentity.generate(fast=True)
        # bundle = bundle_t(roots=[], capsule_list=[], route_list=[])
        # master_peer.make_parcel(bundle, my_identity, services.ref_registry)
        services.transport.send(None)
