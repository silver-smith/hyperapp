import logging

from hyperapp.common.module import Module

from . import htypes
from .command import command
from .record_object import RecordObject

log = logging.getLogger(__name__)


class ObjectViewConfig(RecordObject):

    dir_list = [
        *RecordObject.dir_list,
        [htypes.object_view_config.object_view_config_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, mosaic, lcs, async_web, object_factory, view_producer, make_selector_callback_ref):
        object = await object_factory.invite(piece.piece_ref)
        view_state = await async_web.summon(piece.view_state_ref)
        origin_dir = [
            await async_web.summon(ref)
            for ref in piece.origin_dir
            ]
        target_dir = [
            await async_web.summon(ref)
            for ref in piece.target_dir
            ]

        view_piece = lcs.get([htypes.view.view_d('selected'), *target_dir])

        fields_pieces = cls.make_fields_pieces(mosaic, piece, object, target_dir, view_piece)

        self = cls(mosaic, make_selector_callback_ref, object, view_state, origin_dir, target_dir)
        await self.async_init(object_factory, fields_pieces)
        return self

    @classmethod
    def make_fields_pieces(cls, mosaic, piece, object, target_dir, view_piece):
        return {
            'title': object.title,
            'dir': '/'.join(str(p) for p in target_dir),
            'view': str(view_piece),
            'commands': htypes.command_list.object_command_list(piece.piece_ref, piece.view_state_ref),
            }

    def __init__(self, mosaic, make_selector_callback_ref, object, view_state, origin_dir, target_dir):
        super().__init__()
        self._mosaic = mosaic
        self._make_selector_callback_ref = make_selector_callback_ref
        self._object = object
        self._view_state = view_state
        self._origin_dir = origin_dir
        self._target_dir = target_dir

    @property
    def title(self):
        return f"View config for: {self._object.title}"

    @property
    def piece(self):
        return htypes.object_view_config.object_view_config(**self._piece_fields)

    @property
    def _piece_fields(self):
        return {
            'piece_ref': self._mosaic.put(self._object.piece),
            'view_state_ref': self._mosaic.put(self._view_state),
            'origin_dir': [
                self._mosaic.put(piece)
                for piece in self._origin_dir
                ],
            'target_dir': [
                self._mosaic.put(piece)
                for piece in self._target_dir
                ],
            }

    @command
    async def object_commands(self):
        piece_ref = self._mosaic.put(self._object.piece)
        view_state_ref = self._mosaic.put(self._view_state)
        return htypes.command_list.object_command_list(piece_ref, view_state_ref)

    @command
    async def select_target_dir(self):
        def dir_refs(dir):
            return [
                self._mosaic.put(piece)
                for piece in dir
            ]
        dir_list = htypes.dir_list.dir_list([
            dir_refs(dir)
            for dir in [*self._object.dir_list, self._origin_dir]
            ])
        dir_list_ref = self._mosaic.put(dir_list)
        callback_ref = self._make_selector_callback_ref(self.set_target_dir)
        return htypes.selector.selector(dir_list_ref, callback_ref)

    async def set_target_dir(self, view_item):
        log.info("Set target dir: %s", view_item.dir)
        fields = self._piece_fields
        fields['target_dir'] = [
            self._mosaic.put(piece)
            for piece in view_item.dir
            ]
        return htypes.object_view_config.object_view_config(**fields)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._mosaic = services.mosaic
        self._view_producer = services.view_producer

        services.object_registry.register_actor(
            htypes.object_view_config.object_view_config,
            ObjectViewConfig.from_piece,
            services.mosaic,
            services.lcs,
            services.async_web,
            services.object_factory,
            services.view_producer,
            services.make_selector_callback_ref,
            )
        services.view_dir_to_config[(htypes.object.object_d(),)] = self.config_editor_for_object

    async def config_editor_for_object(self, object, view_state, origin_dir):
        dir, view_piece = self._view_producer.pick_view_piece(object, [origin_dir])
        if htypes.view.view_d('selected') in dir:
            target_dir = dir[1:]  # Remove leading view_d('selected').
        else:
            target_dir = object.dir_list[-1]
        return htypes.object_view_config.object_view_config(
            piece_ref=self._mosaic.put(object.piece),
            view_state_ref=self._mosaic.put(view_state),
            origin_dir=[
                self._mosaic.put(piece)
                for piece in origin_dir
                ],
            target_dir=[
                self._mosaic.put(piece)
                for piece in target_dir
                ],
            )
