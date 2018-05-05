import logging

from ..piece_registry import PieceRegistry, PieceResolver
from ..module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'transport.registry'


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.transport_registry = transport_registry = PieceRegistry('transport', services.type_registry_registry)
        services.transport_resolver = PieceResolver(services.async_ref_resolver, transport_registry)
