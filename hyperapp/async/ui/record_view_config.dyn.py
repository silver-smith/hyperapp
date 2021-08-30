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
    def make_fields_pieces(cls, mosaic, piece, object, target_dir, view_piece):
        return {
            **super().make_fields_pieces(mosaic, piece, object, target_dir, view_piece),
            'fields': htypes.record_field_list.record_field_list(
                piece.piece_ref, piece.origin_dir,
                target_dir=[
                    mosaic.put(p)
                    for p in target_dir
                    ],
                ),
            }

    @property
    def piece(self):
        return htypes.record_view_config.record_view_config(**self._piece_fields)

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
