import itertools
import logging
from collections import namedtuple

from hyperapp.common.htypes import tInt
from hyperapp.common.module import Module

from . import htypes
from .command import command
from .ui_object import Object
from .column import Column
from .simple_list_object import SimpleListObject
from .object_command import Command

log = logging.getLogger(__name__)


Item = namedtuple('Item', 'id dir dir_str type view')
AvailableRec = namedtuple('AvailableRec', 'dir view')


class ViewSelector(SimpleListObject):

    @classmethod
    async def from_piece(cls, piece, mosaic, async_web, lcs, command_registry, object_factory, view_factory_registry, make_selector_callback_ref):
        object = await object_factory.invite(piece.piece_ref)
        origin_dir = [
            await async_web.summon(ref)
            for ref in piece.origin_dir
            ]
        self = cls(mosaic, async_web, lcs, view_factory_registry, make_selector_callback_ref, object, origin_dir)
        await self._async_init(command_registry)
        return self

    def __init__(self, mosaic, async_web, lcs, view_factory_registry, make_selector_callback_ref, object, origin_dir):
        super().__init__()
        self._mosaic = mosaic
        self._async_web = async_web
        self._lcs = lcs
        self._view_factory_registry = view_factory_registry
        self._make_selector_callback_ref = make_selector_callback_ref
        self._object = object
        self._origin_dir = origin_dir
        self._item_list = None  # Set by _populate.
        self._id_to_dir = None  # Set by _populate.
        self._selector_command_list = None  # Set by _async_init
        self._populate()

    async def _async_init(self, command_registry):
        command_piece_it = self._lcs.iter_dir_list_values(
            [[*dir, htypes.command.object_selector_commands_d()] for dir in self._object.dir_list]
            )
        self._selector_command_list = [
            await command_registry.animate(piece)
            for piece in command_piece_it
            ]

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
    def command_list(self):
        return [
            *super().command_list,
            *self._selector_command_list,
            ]

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

    def update(self):
        self._populate()
        super().update()

    @property
    def target_object(self):
        return self._object

    @property
    def origin_dir(self):
        return self._origin_dir

    def key_to_dir(self, key):
        return self._id_to_dir[key]

    def _iter_items(self):
        id_it = itertools.count()
        for dir in self._object.dir_list + [self._origin_dir]:
            dir_str = '/'.join(str(element) for element in dir)
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
        dir = self._id_to_dir[current_key]
        piece_ref = self._mosaic.put(self._object.piece)
        list = htypes.available_view_list.available_view_list(piece_ref)
        list_ref = self._mosaic.put(list)
        dir_param = htypes.view_selector.set_view_param_dir(
            dir=[self._mosaic.put(piece) for piece in dir]
            )
        callback_ref = self._make_selector_callback_ref(self.set_view, dir_param=dir_param)
        return htypes.selector.selector(list_ref, callback_ref)

    async def set_view(self, view_item, *, dir_param):
        dir = [
            await self._async_web.summon(ref)
            for ref in dir_param.dir
            ]
        log.info("Set view for %r: %r", dir, view_item.view)
        self._lcs.set([htypes.view.view_d('selected'), *dir], view_item.view, persist=True)
        self.update()
        return self.piece

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
            services.command_registry,
            services.object_factory,
            services.view_factory_registry,
            services.make_selector_callback_ref,
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
