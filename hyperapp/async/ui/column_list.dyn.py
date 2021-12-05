from collections import namedtuple

from hyperapp.common.module import Module

from . import htypes
from .object_command import Command
from .list_object import ListObject
from .simple_list_object import SimpleListObject


Item = namedtuple('Item', 'name visible')


class ColumnList(SimpleListObject):

    dir_list = [
        *SimpleListObject.dir_list,
        [htypes.column_list.column_list_d()],
        ]

    @classmethod
    async def from_piece(cls, piece, mosaic, lcs, object_factory):
        object = await object_factory.invite(piece.piece_ref)
        return cls(mosaic, lcs, object)

    def __init__(self, mosaic, lcs, object):
        super().__init__()
        self._mosaic = mosaic
        self._lcs = lcs
        self._object = object

    @property
    def title(self):
        return f"Columns for: {self._object.title}"

    @property
    def piece(self):
        piece_ref = self._mosaic.put(self._object.piece)
        return htypes.column_list.column_list(piece_ref)

    @property
    def key_attribute(self):
        return 'name'

    async def get_all_items(self):
        return []


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        self._mosaic = services.mosaic

        services.object_registry.register_actor(
            htypes.column_list.column_list,
            ColumnList.from_piece,
            services.mosaic,
            services.lcs,
            services.object_factory,
            )
        services.lcs.add(
            [*ListObject.dir_list[-1], htypes.command.object_commands_d()],
            htypes.column_list.column_list_command(),
            )
        services.command_registry.register_actor(
            htypes.column_list.column_list_command, Command.from_fn(self.name, self.column_list))

    async def column_list(self, object, view_state, origin_dir):
        piece_ref = self._mosaic.put(object.piece)
        return htypes.column_list.column_list(piece_ref)
