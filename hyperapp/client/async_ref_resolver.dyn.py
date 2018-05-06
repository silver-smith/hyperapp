import logging

from ..common.util import full_type_name_to_str
from ..common.packet_coders import packet_coders
from .module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'async_ref_resolver'


class AsyncRefResolver(object):

    def __init__(self, types, ref_resolver):
        self._types = types
        self._ref_resolver = ref_resolver
        self._async_sources = []

    async def resolve_ref(self, ref):
        piece = self._ref_resolver.resolve_ref(ref)
        if piece:
            return piece
        for source in self._async_sources:
            piece = await source.resolve_ref(ref)
            if piece:
                return piece
        log.debug('ref resolver: ref resolved to %r', piece)
        assert piece, repr(piece)
        return piece

    async def resolve_ref_to_object(self, ref, expected_type=None):
        piece = await self.resolve_ref(ref)
        if expected_type:
            assert full_type_name_to_str(piece.full_type_name) == expected_type
        t = self._types.resolve(piece.full_type_name)
        return packet_coders.decode(piece.encoding, piece.encoded_object, t)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.async_ref_resolver = AsyncRefResolver(services.types, services.ref_resolver)
