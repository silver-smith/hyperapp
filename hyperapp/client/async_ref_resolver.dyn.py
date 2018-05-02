import logging

from ..common.packet_coders import packet_coders
from .module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'async_ref_resolver'


class AsyncRefResolver(object):

    def __init__(self, type_registry_registry, ref_resolver):
        self._type_registry_registry = type_registry_registry
        self._ref_resolver = ref_resolver
        self._async_sources = []

    async def resolve_ref(self, ref):
        referred = self._ref_resolver.resolve_ref(ref)
        if referred:
            return referred
        for source in self._async_sources:
            referred = await source.resolve_ref(ref)
            if referred:
                return referred
        log.debug('ref resolver: ref resolved to %r', referred)
        assert referred, repr(referred)
        return referred

    async def resolve_ref_to_object(self, ref):
        referred = await self.resolve_ref(ref)
        t = self._type_registry_registry.resolve_type(referred.full_type_name)
        return packet_coders.decode(referred.encoding, referred.encoded_object, t)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.async_ref_resolver = AsyncRefResolver(services.type_registry_registry, services.ref_resolver)
