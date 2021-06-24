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
    async def from_state(cls, state, mosaic, async_web, lcs, object_animator, object_commands_factory):
        object = await object_animator.invite(state.piece_ref)
        self = cls(mosaic, lcs, object)
        await self._async_init(object_commands_factory)
        return self

    def __init__(self, mosaic, lcs, object):
        super().__init__()
        self._mosaic = mosaic
        self._lcs = lcs
        self._object = object
        self._command_dict = None
        self._command_shortcut_d_ref = mosaic.put(htypes.command.command_shortcut_d())

    async def _async_init(self, object_commands_factory):
        command_list = await object_commands_factory.get_object_command_list(self._object)
        self._command_dict = {
            command.name: command
            for command in command_list
            }
        # todo: add/pass current item to command list constructor/data, use it here.
        # todo: add state to views; pass it to command list; use it here instead of item key.
        self._item_key = await self._object.first_item_key()

    @property
    def title(self):
        return f"Commands for: {self._object.title}"

    @property
    def piece(self):
        piece_ref = self._mosaic.put(self._object.piece)
        return htypes.command_list.command_list(piece_ref)

    @property
    def columns(self):
        return [
            Column('name', is_key=True),
            Column('shortcut'),
            ]

    async def get_all_items(self):
        return [
            await self._make_item(command)
            for command in self._command_dict.values()
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
        command = self._command_dict[current_key]
        command_ref = self._mosaic.put(command.piece)
        shortcut = run_input_key_dialog()
        if shortcut:
            log.info("Shortcut: %r", shortcut)
            self._lcs.set([[command_ref, self._command_shortcut_d_ref]], shortcut)

    async def _command_handle(self, command, object_type):
        return (await self._layout_handle.command_handle(command.id, object_type))

    async def _run_command(self, command_id):
        command = self._id_to_layout_command[command_id]
        command = command.with_(layout_handle=self._layout_handle)
        resolved_piece = await command.run()
        return resolved_piece

    @command
    async def _run(self, item_key):
        command_id = item_key
        return (await self._run_command(command_id))

    @command
    async def _open_layout(self, item_key):
        command_id = item_key
        command = self._command_dict[command_id]
        if command.code_id == 'self':
            object_type = self._layout_handle.object_type
        else:
            object_type = self._command_object_types[command.code_id]
            if object_type is None:
                # Associating layout to dynamic-object-type command is forbidden. Even if we can run command to get it.
                return None
        object_type_ref = self._mosaic.put(object_type)
        origin_object_type_ref = self._mosaic.put(self._layout_handle.object_type)
        return htypes.layout_editor.object_layout_editor(object_type_ref, origin_object_type_ref, command_id)

    @command
    async def _add_command(self, path):
        piece_ref = self._mosaic.put(self._object.piece)
        layout_ref = self._mosaic.put(self._layout.piece)
        chooser = htypes.code_command_chooser.code_command_chooser(piece_ref, layout_ref)
        chooser_ref = self._mosaic.put(chooser)
        code_command_id_field = htypes.params_editor.field('code_command_id', chooser_ref)
        return htypes.params_editor.params_editor(
            target_piece_ref=self._mosaic.put(self.piece),
            target_command_id=self._add_command_impl.id,
            bound_arguments=[],
            fields=[code_command_id_field],
            )

    @command
    async def _add_command_impl(self, code_command_id):
        new_command_id = self._make_command_id_unique(code_command_id)
        command = self._layout.add_command(self._object, new_command_id, code_command_id)
        self._command_dict[command.id] = command
        self._object_layout_association.associate_type(self._layout_handle.object_type, self._layout)
        return self.piece

    def _make_command_id_unique(self, command_id):
        if command_id not in self._command_dict:
            return command_id
        for idx in itertools.count():
            unique_id = f'{command_id}_{idx}'
            if unique_id not in self._command_dict:
                return unique_id


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        self._mosaic = services.mosaic
        services.object_registry.register_actor(
            htypes.command_list.command_list,
            CommandList.from_state,
            services.mosaic,
            services.async_web,
            services.lcs,
            services.object_animator,
            services.object_commands_factory,
            )
        command_list_cmd_ref = services.mosaic.put(htypes.command_list.command_list_command())
        services.lcs.add([[*Object.dir_list[-1], htypes.command.object_commands_d]], command_list_cmd_ref)
        services.command_registry.register_actor(htypes.command_list.command_list_command, Command.from_fn(self.command_list))

    async def command_list(self, object):
        piece_ref = self._mosaic.put(object.piece)
        return htypes.command_list.command_list(piece_ref)
