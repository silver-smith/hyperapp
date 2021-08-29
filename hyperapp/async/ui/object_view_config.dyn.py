from hyperapp.common.module import Module

from . import htypes
from .command import command
from .record_object import RecordObject


class ObjectViewConfig(RecordObject):

    dir_list = [
        *RecordObject.dir_list,
        [htypes.object_view_config.object_view_config_d()],
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
            }

        self = cls(mosaic, object, view_state, origin_dir, target_dir)
        await self.async_init(object_factory, fields_pieces)
        return self

    def __init__(self, mosaic, object, view_state, origin_dir, target_dir):
        super().__init__()
        self._mosaic = mosaic
        self._object = object
        self._view_state = view_state
        self._origin_dir = origin_dir
        self._target_dir = target_dir

    @property
    def title(self):
        return f"View config for: {self._object.title}"

    @property
    def piece(self):
        return htypes.object_view_config.object_view_config(
            piece_ref=self._mosaic.put(self._object.piece),
            view_state_ref=self._mosaic.put(self._view_state),
            origin_dir=[
                self._mosaic.put(piece)
                for piece in self._origin_dir
                ],
            )

    @command
    async def object_commands(self):
        piece_ref = self._mosaic.put(self._object.piece)
        view_state_ref = self._mosaic.put(self._view_state)
        return htypes.command_list.object_command_list(piece_ref, view_state_ref)

    @command
    async def object_view_selector(self):
        return htypes.view_selector.view_selector(
            piece_ref=self._mosaic.put(self._object.piece),
            origin_dir=[
                self._mosaic.put(piece)
                for piece in self._origin_dir
                ],
            )


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._mosaic = services.mosaic

        services.object_registry.register_actor(
            htypes.object_view_config.object_view_config,
            ObjectViewConfig.from_piece,
            services.mosaic,
            services.async_web,
            services.object_factory,
            services.view_producer,
            )
        services.view_dir_to_config[(htypes.object.object_d(),)] = self.config_editor_for_object

    async def config_editor_for_object(self, object, view_state, origin_dir):
        return htypes.object_view_config.object_view_config(
            piece_ref=self._mosaic.put(object.piece),
            view_state_ref=self._mosaic.put(view_state),
            origin_dir=[
                self._mosaic.put(piece)
                for piece in origin_dir
                ],
            )
