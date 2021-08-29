from hyperapp.common.module import Module

from . import htypes
from .record_object import RecordObject


class ObjectViewConfig(RecordObject):

    dir_list = [
        *RecordObject.dir_list,
        [htypes.object_view_config.object_view_config_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, mosaic, object_factory):
        object = await object_factory.invite(piece.piece_ref)
        fields_pieces = {
            'title': object.title,
            }
        self = cls(mosaic, object)
        await self.async_init(object_factory, fields_pieces)
        return self

    def __init__(self, mosaic, object):
        super().__init__()
        self._mosaic = mosaic
        self._object = object

    @property
    def title(self):
        return f"View config for: {self._object.title}"

    @property
    def piece(self):
        return htypes.object_view_config.object_view_config(
            piece_ref=self._mosaic.put(self._object.piece),
            )


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._mosaic = services.mosaic

        services.object_registry.register_actor(
            htypes.object_view_config.object_view_config,
            ObjectViewConfig.from_piece,
            services.mosaic,
            services.object_factory,
            )
        services.view_dir_to_config[(htypes.object.object_d(),)] = self.config_editor_for_object

    async def config_editor_for_object(self, object):
        return htypes.object_view_config.object_view_config(
            piece_ref=self._mosaic.put(object.piece),
            )
