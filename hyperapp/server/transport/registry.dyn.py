import logging

from ..registry import PieceRegistry, PieceResolver
from ..module import ServerModule

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.registry'


class ThisModule(ServerModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.transport_registry = transport_registry = PieceRegistry('transport', services.types)
        services.transport_resolver = PieceResolver(services.ref_resolver, transport_registry)
