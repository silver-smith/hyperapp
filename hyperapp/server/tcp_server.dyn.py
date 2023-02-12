import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        server_peer_ref = services.mosaic.put(services.server_identity.peer.piece)
        self._tcp_server = server = services.tcp_server_factory(config.get('bind_address'))
        services.route_table.add_route(server_peer_ref, server.route)
        log.info("Server tcp route: %r", server.route)
