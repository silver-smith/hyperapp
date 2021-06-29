import logging
from collections import namedtuple

from hyperapp.common.module import Module

from . import htypes
from .command import command
from .object import Object
from .column import Column
from .simple_list_object import SimpleListObject
from .object_command import Command

log = logging.getLogger(__name__)


Item = namedtuple('Item', 'key dir dir_str type view')


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
        self._item_list = []
        self._available_key_to_dir = {}
        self._populate()

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
            Column('dir_str'),
            Column('type'),
            Column('view'),
            ]

    async def get_all_items(self):
        return self._item_list

    def _populate(self):
        self._item_list = list(self._iter_items())
        self._available_key_to_dir = {
            item.key: item.dir
            for item in self._item_list
            if item.type == 'available'
            }

    def update(self):
        self._populate()
        self._notify_object_changed()

    def _iter_items(self):
        for dir in self._object.dir_list:
            dir_str = '/'.join(str(element) for element in dir)
            key = dir_str
            piece = self._lcs.get(dir)
            if piece is not None:
                yield Item(f'{key}-default', dir, dir_str, 'default', piece)
            piece = self._lcs.get([htypes.view.available_view_d(), *dir])
            if piece is not None:
                yield Item(f'{key}-available', dir, dir_str, 'available', piece)
            yield Item(f'{key}-selected', dir, dir_str, 'selected', '')

    @command
    async def set_default(self, current_key):
        dir = self._available_key_to_dir.get(current_key)
        log.info("Available dir for %s: %r", current_key, dir)
        if not dir:
            return
        piece = self._lcs.get([htypes.view.available_view_d(), *dir])
        assert piece is not None
        self._lcs.set(dir, piece, save=True)
        self.update()


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
