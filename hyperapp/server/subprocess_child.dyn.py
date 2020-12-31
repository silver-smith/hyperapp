from hyperapp.common.htypes import ref_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

from .subprocess_connection import SubprocessRoute


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)

        master_peer_ref_cdr_list = config.get('master_peer_ref_cdr_list', [])
        master_peer_ref_list = [
            packet_coders.decode('cdr', ref_cdr, ref_t)
            for ref_cdr in master_peer_ref_cdr_list
            ]

        master_process_route = SubprocessRoute(services.ref_registry, services.ref_collector_factory, services.master_process_connection)
        for peer_ref in master_peer_ref_list:
            services.route_a9n_registry.associate(peer_ref, master_process_route)
