import logging
from collections import namedtuple

from hyperapp.common.module import Module

from . import htypes
from .command import command
from .record_object import RecordObject
from .column import Column
from .simple_list_object import SimpleListObject
from .object_command import Command

log = logging.getLogger(__name__)


Item = namedtuple('Item', 'id view')


class RecordFieldList(SimpleListObject):

    dir_list = [
        *SimpleListObject.dir_list,
        [htypes.record_field_list.record_field_list_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, mosaic, lcs, object_factory, view_factory, make_selector_callback_ref):
        object = await object_factory.invite(piece.piece_ref)
        return cls(mosaic, lcs, view_factory, make_selector_callback_ref, object)

    def __init__(self, mosaic, lcs, view_factory, make_selector_callback_ref, object):
        super().__init__()
        self._mosaic = mosaic
        self._lcs = lcs
        self._view_factory = view_factory
        self._make_selector_callback_ref = make_selector_callback_ref
        self._object = object

    @property
    def piece(self):
        piece_ref = self._mosaic.put(self._object.piece)
        return htypes.record_field_list.record_field_list(piece_ref)

    @property
    def title(self):
        return f"Fields for record: {self._object.title}"

    @property
    def columns(self):
        return [
            Column('id', is_key=True),
            Column('view'),
            ]

    async def get_all_items(self):
        return list(self._iter_items())

    def _iter_items(self):
        for field_id, field in self._object.fields.items():
            dir_list = self._object.record_field_dir_list(field_id, field)
            view_piece = self._view_factory.pick_view_piece(dir_list)
            yield Item(field_id, view_piece)

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
        dir = self._object.record_field_dir(field_id, field)  # todo: allow to select dir to set view for.
        self._lcs.set(dir, view_item.view)
        return self.piece


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._mosaic = services.mosaic

        services.object_registry.register_actor(
            htypes.record_field_list.record_field_list,
            RecordFieldList.from_piece,
            services.mosaic,
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
        return htypes.record_field_list.record_field_list(piece_ref)
