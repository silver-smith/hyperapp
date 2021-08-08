import logging
from collections import namedtuple

from hyperapp.common.module import Module

from . import htypes
from .command import command
from .record_object import RecordObject, record_field_dir, record_field_add_dir_list
from .column import Column
from .simple_list_object import SimpleListObject
from .object_command import Command

log = logging.getLogger(__name__)


Item = namedtuple('Item', 'id dir view')


class RecordFieldList(SimpleListObject):

    dir_list = [
        *SimpleListObject.dir_list,
        [htypes.record_field_list.record_field_list_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, mosaic, async_web, lcs, object_factory, view_factory, make_selector_callback_ref):
        object = await object_factory.invite(piece.piece_ref)
        origin_dir = [
            await async_web.summon(ref)
            for ref in piece.origin_dir
            ]
        target_dir = [
            await async_web.summon(ref)
            for ref in piece.target_dir
            ]
        return cls(mosaic, lcs, view_factory, make_selector_callback_ref, object, origin_dir, target_dir)

    def __init__(self, mosaic, lcs, view_factory, make_selector_callback_ref, object, origin_dir, target_dir):
        super().__init__()
        self._mosaic = mosaic
        self._lcs = lcs
        self._view_factory = view_factory
        self._make_selector_callback_ref = make_selector_callback_ref
        self._object = object
        self._origin_dir = origin_dir
        self._target_dir = target_dir

    @property
    def piece(self):
        piece_ref = self._mosaic.put(self._object.piece)
        origin_dir_refs = tuple(
            self._mosaic.put(piece)
            for piece in self._origin_dir
            )
        target_dir_refs = tuple(
            self._mosaic.put(piece)
            for piece in self._target_dir
            )
        return htypes.record_field_list.record_field_list(piece_ref, origin_dir_refs, target_dir_refs)

    @property
    def title(self):
        return f"Fields for record: {self._object.title}"

    @property
    def columns(self):
        return [
            Column('id', is_key=True),
            Column('dir'),
            Column('view'),
            ]

    async def get_all_items(self):
        return list(self._iter_items())

    def _iter_items(self):
        record_dir_list = [*self._object.dir_list, self._origin_dir]
        for field_id, field in self._object.fields.items():
            add_dir_list = record_field_add_dir_list(record_dir_list, field_id, field)
            dir, view_piece = self._view_factory.pick_view_piece(field, add_dir_list)
            dir_str = '/'.join(str(v) for v in dir)
            yield Item(field_id, dir_str, view_piece)

    @command
    async def select(self, current_key):
        field_id = current_key
        field = self._object.fields[field_id]
        piece_ref = self._mosaic.put(field.piece)
        list = htypes.available_view_list.available_view_list(piece_ref)
        list_ref = self._mosaic.put(list)
        callback_ref = self._make_selector_callback_ref(self.set_view, field_id=field_id)
        return htypes.selector.selector(list_ref, callback_ref)

    async def set_view(self, view_item, *, field_id):
        log.info("Set view for %r: %r", field_id, view_item.view)
        field = self._object.fields[field_id]
        dir = record_field_dir(self._target_dir, field_id, field)
        self._lcs.set([htypes.view.view_d('selected'), *dir], view_item.view)
        return self.piece


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._mosaic = services.mosaic

        services.object_registry.register_actor(
            htypes.record_field_list.record_field_list,
            RecordFieldList.from_piece,
            services.mosaic,
            services.async_web,
            services.lcs,
            services.object_factory,
            services.view_factory,
            services.make_selector_callback_ref,
            )
        services.command_registry.register_actor(
            htypes.record_field_list.open_record_field_list_command, Command.from_fn(self.name, self.record_field_list))
        services.lcs.add(
            [*RecordObject.dir_list[-1], htypes.command.object_selector_commands_d()],
            htypes.record_field_list.open_record_field_list_command(),
            )

    async def record_field_list(self, object, view_state, origin_dir):
        piece_ref = self._mosaic.put(object.target_object.piece)
        target_dir = object.key_to_dir(view_state.current_key)
        origin_dir_refs = tuple(
            self._mosaic.put(piece)
            for piece in object.origin_dir
            )
        target_dir_refs = tuple(
            self._mosaic.put(piece)
            for piece in target_dir
            )
        return htypes.record_field_list.record_field_list(piece_ref, origin_dir_refs, target_dir_refs)
