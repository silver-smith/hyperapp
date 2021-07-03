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


Item = namedtuple('Item', 'name view')


class RecordFieldList(SimpleListObject):

    dir_list = [
        *SimpleListObject.dir_list,
        [htypes.record_field_list.record_field_list_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, mosaic, lcs, object_animator):
        object = await object_animator.invite(piece.piece_ref)
        return cls(mosaic, lcs, object)

    def __init__(self, mosaic, lcs, object):
        super().__init__()
        self._mosaic = mosaic
        self._lcs = lcs
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
            Column('name', is_key=True),
            Column('view'),
            ]

    async def get_all_items(self):
        return [
            Item(name, self._lcs.get_first(field.dir_list))
            for name, field in self._object.fields.items()
            ]

    @command
    async def select(self, current_key):
        field = self._object.fields[current_key]
        piece_ref = self._mosaic.put(field.piece)
        list = htypes.available_view_list.available_view_list(piece_ref)
        list_ref = self._mosaic.put(list)
        return htypes.selector.selector(list_ref)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._mosaic = services.mosaic

        services.object_registry.register_actor(
            htypes.record_field_list.record_field_list,
            RecordFieldList.from_piece,
            services.mosaic,
            services.lcs,
            services.object_animator,
            )
        services.command_registry.register_actor(
            htypes.record_field_list.open_record_field_list_command, Command.from_fn(self.name, self.record_field_list))
        services.lcs.add(
            [*RecordObject.dir_list[-1], htypes.command.object_commands_d()],
            htypes.record_field_list.open_record_field_list_command(),
            )

    async def record_field_list(self, object, view_state):
        piece_ref = self._mosaic.put(object.piece)
        return htypes.record_field_list.record_field_list(piece_ref)
