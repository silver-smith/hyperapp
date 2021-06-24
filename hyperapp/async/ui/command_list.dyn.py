import itertools
import logging
from collections import namedtuple

from hyperapp.common.module import Module
from hyperapp.common.util import single

from . import htypes
from .column import Column
from .object import Object
from .object_command import Command, command
from .simple_list_object import SimpleListObject
from .qt_keys import run_input_key_dialog

log = logging.getLogger(__name__)


Item = namedtuple('Item', 'name shortcut')


class CommandList(SimpleListObject):

    @classmethod
    async def from_piece(cls, piece, mosaic, async_web, lcs, object_animator, object_commands_factory):
        object = await object_animator.invite(piece.piece_ref)
        view_state = await async_web.summon(piece.view_state_ref)
        self = cls(mosaic, lcs, object, view_state)
        await self._async_init(object_commands_factory)
        return self

    def __init__(self, mosaic, lcs, object, view_state):
        super().__init__()
        self._mosaic = mosaic
        self._lcs = lcs
        self._object = object
        self._view_state = view_state
        self._command_by_name = None
        self._command_shortcut_d_ref = mosaic.put(htypes.command.command_shortcut_d())

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
        return htypes.command_list.command_list(piece_ref, view_state_ref)

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

    @property
    def _layout(self):
        return self._layout_handle.layout

    async def _make_item(self, command):
        command_ref = self._mosaic.put(command.piece)
        try:
            shortcut = self._lcs.get([[command_ref, self._command_shortcut_d_ref]])
        except KeyError:
            shortcut = ''
        return Item(
            name=command.name,
            shortcut=shortcut,
            )

    @command
    async def set_key(self, current_key):
        log.info("Set key for %r", current_key)
        command = self._command_by_name[current_key]
        command_ref = self._mosaic.put(command.piece)
        shortcut = run_input_key_dialog()
        if shortcut:
            log.info("Shortcut: %r", shortcut)
            self._lcs.set([[command_ref, self._command_shortcut_d_ref]], shortcut)
            self._notify_object_changed()

    @command
    async def run(self, current_key):
        command_name = current_key
        command = self._command_by_name[command_name]
        return await command.run(self._object, self._view_state)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._mosaic = services.mosaic
        services.object_registry.register_actor(
            htypes.command_list.command_list,
            CommandList.from_piece,
            services.mosaic,
            services.async_web,
            services.lcs,
            services.object_animator,
            services.object_commands_factory,
            )
        command_list_cmd_ref = services.mosaic.put(htypes.command_list.command_list_command())
        services.lcs.add([[*Object.dir_list[-1], htypes.command.object_commands_d]], command_list_cmd_ref)
        services.command_registry.register_actor(htypes.command_list.command_list_command, Command.from_fn(self.command_list))

    async def command_list(self, object, view_state):
        piece_ref = self._mosaic.put(object.piece)
        view_state_ref = self._mosaic.put(view_state)
        return htypes.command_list.command_list(piece_ref, view_state_ref)
