import logging
import abc

from hyperapp.common.htypes.packet_coders import packet_coders

from .module import ClientModule

log = logging.getLogger(__name__)


class AsyncRefSource(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def pull(self, ref):
        pass


class AsyncWeb(object):

    def __init__(self, web, types):
        self._web = web
        self._types = types
        self._async_sources = []

    def add_async_source(self, source):
        assert isinstance(source, AsyncRefSource), repr(source)
        self._async_sources.append(source)

    async def pull(self, ref):
        capsule = self._web.pull(ref)
        if capsule:
            return capsule
        for source in self._async_sources:
            capsule = await source.pull(ref)
            if capsule:
                return capsule
        log.debug('ref resolver: ref resolved to %r', capsule)
        assert capsule, repr(capsule)
        return capsule

    async def summon(self, ref, expected_type=None):
        capsule = await self.pull(ref)
        t = self._types.resolve(capsule.type_ref)
        if expected_type:
            assert t is expected_type, (t, expected_type)
        return packet_coders.decode(capsule.encoding, capsule.encoded_object, t)

    async def summon_opt(self, ref, expected_type=None):
        if ref is None:
            return None
        return await self.summon(ref, expected_type)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)
        services.async_web = AsyncWeb(services.web, services.types)
