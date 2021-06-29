from collections import namedtuple

from hyperapp.common.module import Module

from . import htypes
from .object import Object
from .column import Column
from .simple_list_object import SimpleListObject
from .object_command import Command


Item = namedtuple('Item', 'key dir type view')


class ViewSelector(SimpleListObject):

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
        return htypes.view_selector.view_selector(piece_ref)

    @property
    def title(self):
        return f"Select view for: {self._object.title}"

    @property
    def columns(self):
        return [
            Column('key', is_key=True),
            Column('dir'),
            Column('type'),
            Column('view'),
            ]

    async def get_all_items(self):
        return list(self._iter_items())

    def _iter_items(self):
        for dir in self._object.dir_list:
            dir_str = '/'.join(str(element) for element in dir)
            key = dir_str
            piece = self._lcs.get(dir)
            if piece is not None:
                yield Item(f'{key}-default', dir_str, 'default', piece)
            piece = self._lcs.get([htypes.view.available_view_d(), *dir])
            if piece is not None:
                yield Item(f'{key}-available', dir_str, 'available', piece)
            yield Item(f'{key}-selected', dir_str, 'selected', '')


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._mosaic = services.mosaic

        services.object_registry.register_actor(
            htypes.view_selector.view_selector,
            ViewSelector.from_piece,
            services.mosaic,
            services.lcs,
            services.object_animator,
            )
        services.command_registry.register_actor(htypes.view_selector.open_view_selector_command, Command.from_fn(self.view_selector))
        services.lcs.add(
            [*Object.dir_list[-1], htypes.command.object_commands_d()],
            htypes.view_selector.open_view_selector_command(),
            )

    async def view_selector(self, object, view_state):
        piece_ref = self._mosaic.put(object.piece)
        return htypes.view_selector.view_selector(piece_ref)
