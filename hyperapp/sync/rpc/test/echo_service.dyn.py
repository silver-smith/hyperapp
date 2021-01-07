from hyperapp.common.htypes import bundle_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

from . import htypes


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)

        master_service_bundle = packet_coders.decode('cdr', config['master_service_bundle_cdr'], bundle_t)
        services.unbundler.register_bundle(master_service_bundle)
        master_service_ref = master_service_bundle.roots[0]
        master_service = services.types.resolve_ref(master_service_ref).value

        my_identity = services.generate_rsa_identity(fast=True)
        my_peer_ref = services.mosaic.distil(my_identity.peer.piece)

        echo_iface_ref = services.types.reverse_resolve(htypes.echo.echo_iface)
        echo_service = htypes.rpc.endpoint(
            peer_ref=my_peer_ref,
            iface_ref=echo_iface_ref,
            object_id='echo',
            )
        echo_service_ref = services.mosaic.distil(echo_service)

        proxy = services.rpc_proxy(my_identity, master_service)
        proxy.run(echo_service_ref)
