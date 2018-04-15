import logging

from hyperapp.common.interface import tcp_transport as tcp_transport_types
from hyperapp.common.ref import make_object_ref
from ..module import Module

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.tcp'

LISTEN_HOST = 'localhost'
LISTEN_PORT = 9999


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, MODULE_NAME)
        route = tcp_transport_types.route(LISTEN_HOST, LISTEN_PORT)
        services.tcp_transport_ref = services.ref_registry.register_object(tcp_transport_types.route, route)
