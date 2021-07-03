import logging

from hyperapp.common.htypes import TRecord, ref_t
from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.ref import decode_capsule
from hyperapp.common.module import Module

from . import htypes
from .code_registry import CodeRegistry, CodeRegistryKeyError
from .record_object import RecordObject

log = logging.getLogger(__name__)


class NotRegisteredError(RuntimeError):
    pass


class RecordViewer(RecordObject):

    def __init__(self, fields, piece, title):
        super().__init__(fields)
        self._piece = piece
        self._title = title

    @property
    def title(self):
        return self._title

    @property
    def piece(self):
        return self._piece


class ObjectAnimator:

    def __init__(self, types, async_web, object_registry):
        self._types = types
        self._async_web = async_web
        self._object_registry = object_registry

    async def animate(self, piece):
        try:
            return await self._object_registry.animate(piece)
        except CodeRegistryKeyError:
            pass
        return await self._construct_object(piece)

    async def invite(self, ref, *args, **kw):
        assert isinstance(ref, ref_t), repr(ref)
        capsule = await self._async_web.pull(ref)
        decoded_capsule = decode_capsule(self._types, capsule)
        return await self.animate(decoded_capsule.value)

    async def _construct_object(self, piece):
        t = deduce_value_type(piece)
        if isinstance(t, TRecord):
            try:
                return await self._construct_record_object(t, piece)
            except NotRegisteredError as x:
                raise NotRegisteredError(f"For record {piece}: {x}")
        raise NotRegisteredError(f"No code is registered for object: {t!r}; piece: {piece}")

    async def _construct_record_object(self, t, piece):
        log.info("Construct object for %s: %s", t, piece)
        fields = {
            name: await self.animate(getattr(piece, name))
            for name in t.fields
            }
        return RecordViewer(fields, piece, title=t.name)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.object_registry = CodeRegistry('object', services.async_web, services.types)
        services.object_animator = ObjectAnimator(services.types, services.async_web, services.object_registry)
