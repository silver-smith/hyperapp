from hyperapp.common.htypes import TRecord
from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.module import Module

from . import htypes
from .code_registry import CodeRegistry, CodeRegistryKeyError
from .record_object import RecordObject


class RecordViewer(RecordObject):

    def __init__(self, fields, object_type, piece, title):
        super().__init__(fields)
        self.type = object_type
        self._piece = piece
        self._title = title

    @property
    def title(self):
        return self._title

    @property
    def piece(self):
        return self._piece


class ObjectAnimator:

    def __init__(self, mosaic, object_registry):
        self._mosaic = mosaic
        self._object_registry = object_registry

    async def animate(self, piece):
        try:
            return await self._object_registry.animate(piece)
        except CodeRegistryKeyError:
            pass
        return await self._construct_object(piece)

    async def _construct_object(self, piece):
        t = deduce_value_type(piece)
        if isinstance(t, TRecord):
            return await self._construct_record_object(t, piece)
        raise RuntimeError(f"No code is registered for object: {t!r}; piece: {piece}")

    async def _construct_record_object(self, t, piece):
        fields = {
            name: await self.animate(getattr(piece, name))
            for name in t.fields
            }
        object_type = htypes.record_object.record_object_type(
            command_list=(),
            field_type_list=tuple(
                htypes.record_object.record_type_field(name, self._mosaic.put(field_object.type))
                for name, field_object in fields.items()
                ),
            )
        return RecordViewer(fields, object_type, piece, title=t.name)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.object_registry = CodeRegistry('object', services.async_web, services.types)
        services.object_animator = ObjectAnimator(services.mosaic, services.object_registry)
