import itertools
import logging
from collections import namedtuple

from hyperapp.common.htypes import tInt
from hyperapp.common.module import Module

from . import htypes
from .command import command
from .object import Object
from .column import Column
from .simple_list_object import SimpleListObject
from .object_command import Command

log = logging.getLogger(__name__)


Item = namedtuple('Item', 'id dir dir_str type view')
AvailableRec = namedtuple('AvailableRec', 'dir view')


class ViewSelector(SimpleListObject):

    @classmethod
    async def from_piece(cls, piece, mosaic, async_web, lcs, object_factory):
        object = await object_factory.invite(piece.piece_ref)
        origin_dir = [
            await async_web.summon(ref)
            for ref in piece.origin_dir
            ]
        return cls(mosaic, lcs, object, origin_dir)

    def __init__(self, mosaic, lcs, object, origin_dir):
        super().__init__()
        self._mosaic = mosaic
        self._lcs = lcs
        self._object = object
        self._origin_dir = origin_dir
        self._item_list = []
        self._id_dir = {}
        self._id_to_available_rec = {}
        self._populate()

    @property
    def piece(self):
        piece_ref = self._mosaic.put(self._object.piece)
        origin_dir_refs = tuple(
            self._mosaic.put(piece)
            for piece in self._origin_dir
            )
        return htypes.view_selector.view_selector(piece_ref, origin_dir_refs)

    @property
    def title(self):
        return f"Select view for: {self._object.title}"

    @property
    def columns(self):
        return [
            Column('id', type=tInt, is_key=True),
            Column('dir_str'),
            Column('type'),
            Column('view'),
            ]

    async def get_all_items(self):
        return self._item_list

    def _populate(self):
        self._item_list = list(self._iter_items())
        self._id_to_dir = {
            item.id: item.dir
            for item in self._item_list
            }
        self._id_to_available_rec = {
            item.id: AvailableRec(item.dir, item.view)
            for item in self._item_list
            if item.type == 'available'
            }

    def update(self):
        self._populate()
        self._notify_object_changed()

    def _iter_items(self):
        id_it = itertools.count()
        for dir in self._object.dir_list + [self._origin_dir]:
            dir_str = '/'.join(str(element) for element in dir)
            for available_piece in self._lcs.iter([[htypes.view.view_d('available'), *dir]]):
                yield Item(next(id_it), dir, dir_str, 'available', available_piece)
            default_piece = self._lcs.get([htypes.view.view_d('default'), *dir])
            if default_piece is not None:
                yield Item(next(id_it), dir, dir_str, 'default', default_piece)
            selected_piece = self._lcs.get([htypes.view.view_d('selected'), *dir])
            if selected_piece is not None:
                yield Item(next(id_it), dir, dir_str, 'selected', selected_piece)
            if selected_piece is None and default_piece is None:
                yield Item(next(id_it), dir, dir_str, '', '')

    @command
    async def select(self, current_key):
        rec = self._id_to_available_rec.get(current_key)
        log.info("Available dir for %d: %r -> %r", current_key, rec.dir, rec.view)
        if not rec:
            return
        self._lcs.set([htypes.view.view_d('selected'), *rec.dir], rec.view, persist=True)
        self.update()

    @command
    async def remove(self, current_key):
        dir = self._id_to_dir[current_key]
        piece = self._lcs.get([htypes.view.view_d('selected'), *dir])
        if piece is None:
            log.info("Dir is not selected: %s", dir)
            return
        self._lcs.remove([htypes.view.view_d('selected'), *dir])
        self.update()


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._mosaic = services.mosaic

        services.object_registry.register_actor(
            htypes.view_selector.view_selector,
            ViewSelector.from_piece,
            services.mosaic,
            services.async_web,
            services.lcs,
            services.object_factory,
            )
        services.command_registry.register_actor(
            htypes.view_selector.open_view_selector_command, Command.from_fn(self.name, self.view_selector))
        services.lcs.add(
            [*Object.dir_list[-1], htypes.command.object_commands_d()],
            htypes.view_selector.open_view_selector_command(),
            )

    async def view_selector(self, object, view_state, origin_dir):
        piece_ref = self._mosaic.put(object.piece)
        origin_dir_refs = tuple(
            self._mosaic.put(piece)
            for piece in origin_dir
            )
        return htypes.view_selector.view_selector(piece_ref, origin_dir_refs)
