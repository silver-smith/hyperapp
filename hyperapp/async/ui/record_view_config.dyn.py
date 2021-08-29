from hyperapp.common.module import Module

from . import htypes
from .command import command
from .object_view_config import ObjectViewConfig


class RecordViewConfig(ObjectViewConfig):

    dir_list = [
        *ObjectViewConfig.dir_list,
        [htypes.record_view_config.record_view_config_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, mosaic, async_web, object_factory, view_producer):
        object = await object_factory.invite(piece.piece_ref)
        view_state = await async_web.summon(piece.view_state_ref)
        origin_dir = [
            await async_web.summon(ref)
            for ref in piece.origin_dir
            ]

        target_dir, view_piece = view_producer.pick_view_piece(object, [origin_dir])

        fields_pieces = {
            'title': object.title,
            'dir': '/'.join(str(p) for p in target_dir),
            'view': str(view_piece),
            'commands': htypes.command_list.object_command_list(piece.piece_ref, piece.view_state_ref),
            'fields': htypes.record_field_list.record_field_list(
                piece.piece_ref, piece.origin_dir,
                target_dir=[
                    mosaic.put(piece)
                    for p in target_dir
                    ],
                ),
            }

        self = cls(mosaic, object, view_state, origin_dir, target_dir)
        await self.async_init(object_factory, fields_pieces)
        return self

    @property
    def piece(self):
        return htypes.record_view_config.record_view_config(
            piece_ref=self._mosaic.put(self._object.piece),
            view_state_ref=self._mosaic.put(self._view_state),
            origin_dir=[
                self._mosaic.put(piece)
                for piece in self._origin_dir
                ],
            )

    @command
    async def object_field_list(self):
        return htypes.record_field_list.record_field_list(
            piece_ref=self._mosaic.put(self._object.piece),
            origin_dir=[
                self._mosaic.put(piece)
                for piece in self._origin_dir
                ],
            target_dir=[
                self._mosaic.put(piece)
                for piece in self._target_dir
                ],
            )


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._mosaic = services.mosaic

        services.object_registry.register_actor(
            htypes.record_view_config.record_view_config,
            RecordViewConfig.from_piece,
            services.mosaic,
            services.async_web,
            services.object_factory,
            services.view_producer,
            )
        services.view_dir_to_config[(htypes.record_object.record_object_d(),)] = self.config_editor_for_record_object

    async def config_editor_for_record_object(self, object, view_state, origin_dir):
        return htypes.record_view_config.record_view_config(
            piece_ref=self._mosaic.put(object.piece),
            view_state_ref=self._mosaic.put(view_state),
            origin_dir=[
                self._mosaic.put(piece)
                for piece in origin_dir
                ],
            )
