import asyncio
import itertools
import logging
from collections import namedtuple

from hyperapp.common.util import single

from . import htypes
from .column import Column
from .object import Object
from .command import command
from .object_command import Command
from .simple_list_object import SimpleListObject
from .qt_keys import run_input_key_dialog
from .module import ClientModule

log = logging.getLogger(__name__)


Item = namedtuple('Item', 'name shortcut')
ViewItem = namedtuple('Item', 'name path shortcut')


class CommandList(SimpleListObject):

    def __init__(self, lcs):
        super().__init__()
        self._lcs = lcs
        self._command_by_name = None

    @property
    def columns(self):
        return [
            Column('name', is_key=True),
            Column('shortcut'),
            ]

    async def get_all_items(self):
        return [
            await self._make_item(command)
            for command in self._command_by_name.values()
            ]

    async def _make_item(self, command):
        shortcut = self._command_shortcut(command) or ''
        return Item(
            name=command.name,
            shortcut=shortcut or '',
            )

    def _command_shortcut(self, command):
        return self._lcs.get([command.piece, htypes.command.command_shortcut_d()])

    @command
    async def set_key(self, current_key):
        shortcut = run_input_key_dialog()
        if shortcut:
            await self._set_key(current_key, shortcut)

    @command
    async def set_key_escape(self, current_key):
        await self._set_key(current_key, 'Escape')

    async def _set_key(self, command_name, shortcut):
        log.info("Set shortcut for command %s: %r", command_name, shortcut)
        command = self._command_by_name[command_name]
        self._lcs.set([command.piece, htypes.command.command_shortcut_d()], shortcut, save=True)
        await self.update()

    @command
    async def run(self, current_key):
        command_name = current_key
        command = self._command_by_name[command_name]
        return await self._run(command)

    async def _run(self, command):
        return await command.run()

    async def update(self):
        self._notify_object_changed()


class ObjectCommandList(CommandList):

    @classmethod
    async def from_piece(cls, piece, mosaic, async_web, lcs, object_animator, object_commands_factory):
        object = await object_animator.invite(piece.piece_ref)
        view_state = await async_web.summon(piece.view_state_ref)
        self = cls(mosaic, lcs, object, view_state)
        await self._async_init(object_commands_factory)
        return self

    def __init__(self, mosaic, lcs, object, view_state):
        super().__init__(lcs)
        self._mosaic = mosaic
        self._object = object
        self._view_state = view_state

    async def _async_init(self, object_commands_factory):
        command_list = await object_commands_factory.get_object_command_list(self._object)
        self._command_by_name = {
            command.name: command
            for command in command_list
            }

    @property
    def title(self):
        return f"Commands for: {self._object.title}"

    @property
    def piece(self):
        piece_ref = self._mosaic.put(self._object.piece)
        view_state_ref = self._mosaic.put(self._view_state)
        return htypes.command_list.object_command_list(piece_ref, view_state_ref)

    async def _run(self, command):
        return await command.run(self._object, self._view_state)


class GlobalCommandList(CommandList):

    @classmethod
    async def from_piece(cls, piece, async_web, lcs, global_command_list, layout_manager):
        return cls(lcs, global_command_list, layout_manager)

    def __init__(self, lcs, global_command_list, layout_manager):
        super().__init__(lcs)
        self._layout_manager = layout_manager
        self._command_by_name = {
            command.name: command
            for command in global_command_list
            }

    @property
    def title(self):
        return "Global commands"

    @property
    def piece(self):
        return htypes.command_list.global_command_list()

    async def update(self):
        await super().update()
        await self._layout_manager.root_layout.update_commands()


class ViewCommandList(CommandList):

    @classmethod
    async def from_piece(cls, piece, async_web, lcs, layout_manager):
        self = cls(lcs, layout_manager)
        # When this object is current on client start, layout_manager is not yet fully constructed.
        # Postpone it's usage until layout_manager.root_layout is set.
        asyncio.get_event_loop().call_soon(self._post_init)
        return self

    def __init__(self, lcs, layout_manager):
        super().__init__(lcs)
        self._layout_manager = layout_manager
        self._path_by_name = None

    def _post_init(self):
        view_commands = self._layout_manager.root_layout.collect_view_commands()
        self._command_by_name = {
            command.name: command
            for (path, command) in view_commands
            }
        self._path_by_name = {
            command.name: path
            for (path, command) in view_commands
            }

    @property
    def title(self):
        return "View commands"

    @property
    def piece(self):
        return htypes.command_list.view_command_list()

    @property
    def columns(self):
        return [
            Column('name', is_key=True),
            Column('path'),
            Column('shortcut'),
            ]

    async def _make_item(self, command):
        shortcut = self._command_shortcut(command) or ''
        return ViewItem(
            name=command.name,
            path='/'.join(self._path_by_name[command.name]),
            shortcut=shortcut or '',
            )

    async def update(self):
        await super().update()
        await self._layout_manager.root_layout.update_commands()


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._mosaic = services.mosaic
        services.object_registry.register_actor(
            htypes.command_list.object_command_list,
            ObjectCommandList.from_piece,
            services.mosaic,
            services.async_web,
            services.lcs,
            services.object_animator,
            services.object_commands_factory,
            )
        services.object_registry.register_actor(
            htypes.command_list.global_command_list,
            GlobalCommandList.from_piece,
            services.async_web,
            services.lcs,
            services.global_command_list,
            services.layout_manager,
            )
        services.object_registry.register_actor(
            htypes.command_list.view_command_list,
            ViewCommandList.from_piece,
            services.async_web,
            services.lcs,
            services.layout_manager,
            )
        services.lcs.add(
            [*Object.dir_list[-1], htypes.command.object_commands_d()],
            htypes.command_list.command_list_command(),
            )
        services.command_registry.register_actor(htypes.command_list.command_list_command, Command.from_fn(self.command_list))

    async def command_list(self, object, view_state):
        piece_ref = self._mosaic.put(object.piece)
        view_state_ref = self._mosaic.put(view_state)
        return htypes.command_list.object_command_list(piece_ref, view_state_ref)

    @command
    async def global_commands(self):
        return htypes.command_list.global_command_list()

    @command
    async def view_commands(self):
        return htypes.command_list.view_command_list()
