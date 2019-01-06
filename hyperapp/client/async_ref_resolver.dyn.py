import logging
import abc

from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.client.module import ClientModule

log = logging.getLogger(__name__)


MODULE_NAME = 'async_ref_resolver'


class AsyncRefSource(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def resolve_ref(self, ref):
        pass


class AsyncRefResolver(object):

    def __init__(self, ref_resolver, type_resolver):
        self._ref_resolver = ref_resolver
        self._type_resolver = type_resolver
        self._async_sources = []

    def add_async_source(self, source):
        assert isinstance(source, AsyncRefSource), repr(source)
        self._async_sources.append(source)

    async def resolve_ref(self, ref):
        capsule = self._ref_resolver.resolve_ref(ref)
        if capsule:
            return capsule
        for source in self._async_sources:
            capsule = await source.resolve_ref(ref)
            if capsule:
                return capsule
        log.debug('ref resolver: ref resolved to %r', capsule)
        assert capsule, repr(capsule)
        return capsule

    async def resolve_ref_to_object(self, ref, expected_type=None):
        capsule = await self.resolve_ref(ref)
        t = self._type_resolver.resolve(capsule.type_ref)
        if expected_type:
            assert t is expected_type, (t, expected_type)
        return packet_coders.decode(capsule.encoding, capsule.encoded_object, t)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.async_ref_resolver = AsyncRefResolver(services.ref_resolver, services.type_resolver)
