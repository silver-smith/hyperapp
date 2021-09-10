import logging

from hyperapp.common.htypes import ref_t
from hyperapp.common.ref import decode_capsule
from hyperapp.common.module import Module

from . import htypes
from .code_registry import CodeRegistry, CodeRegistryKeyError

log = logging.getLogger(__name__)


class NotRegisteredError(RuntimeError):
    pass


class Holder:

    def __init__(self):
        self._value = None

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


class ObjectFactory:

    def __init__(self, types, async_web, object_registry, default_object_factory):
        self._types = types
        self._async_web = async_web
        self._object_registry = object_registry
        self._default_object_factory = default_object_factory

    async def animate(self, piece):
        try:
            return await self._object_registry.animate(piece)
        except CodeRegistryKeyError:
            pass
        factory = self._default_object_factory.get()
        return await factory(piece)

    async def invite(self, ref, *args, **kw):
        assert isinstance(ref, ref_t), repr(ref)
        capsule = await self._async_web.pull(ref)
        decoded_capsule = decode_capsule(self._types, capsule)
        return await self.animate(decoded_capsule.value)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.object_registry = CodeRegistry('object', services.async_web, services.types)
        services.default_object_factory = Holder()
        services.object_factory = ObjectFactory(services.types, services.async_web, services.object_registry, services.default_object_factory)
