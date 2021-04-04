import itertools
from collections import namedtuple

from hyperapp.common.util import single

from . import htypes
from .command import command
from .column import Column
from .object_command import command as object_command
from .layout_handle import LayoutWatcher
from .simple_list_object import SimpleListObject
from .module import ClientModule


Item = namedtuple('Item', 'id code_id kind path layout')


class CommandList(SimpleListObject):

    @classmethod
    async def from_state(cls, state, mosaic, async_web, object_registry, object_layout_association, layout_handle_from_ref, layout_handle_from_object_type):
        piece = await async_web.summon(state.piece_ref)
        object = await object_registry.animate(piece)
        layout_handle = await layout_handle_from_ref(state.layout_handle_ref)
        self = cls(mosaic, object_layout_association, layout_handle_from_object_type, object, layout_handle)
        await self._async_init(async_web)
        return self

    def __init__(self, mosaic, object_layout_association, layout_handle_from_object_type, object, layout_handle):
        super().__init__()
        self._mosaic = mosaic
        self._object_layout_association = object_layout_association
        self._layout_handle_from_object_type = layout_handle_from_object_type
        self._object = object
        self._layout_handle = layout_handle
        self._command_dict = {
            command.id: command
            for command in self._layout.command_list
            }
        self._id_to_path_and_code_command = {
            command.id: (path, command)
            for path, command in self._layout.available_code_commands(self._object)
            }

    async def _async_init(self, async_web):
        self._command_object_types = {
            command.id: await async_web.summon(command.result_object_type_ref)
            for command in self._object.type.command_list
            }
        # todo: add/pass current item to command list constructor/data, use it here.
        # todo: add state to views; pass it to command list; use it here instead of item key.
        self._item_key = await self._object.first_item_key()
        self._id_to_layout_command = {
            command.id: command
            for command in self._layout.get_item_commands(self._object, self._item_key)
            }

    @property
    def title(self):
        return f"Commands for: {self._layout_handle.object_type._t.name}"

    @property
    def piece(self):
        piece_ref = self._mosaic.put(self._object.piece)
        layout_handle_ref = self._mosaic.put(self._layout_handle.piece)
        return htypes.command_list.command_list(piece_ref, layout_handle_ref)

    @property
    def columns(self):
        return [
            Column('id', is_key=True),
            Column('code_id'),
            Column('kind'),
            Column('path'),
            Column('layout'),
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
        if command.code_id == 'self':
            object_type = self._layout_handle.object_type
            path = []
            kind = 'object'
        else:
            object_type = self._command_object_types[command.code_id]
            path, code_command = self._id_to_path_and_code_command[command.code_id]
            kind = code_command.kind
        if object_type is not None:
            layout_handle = await self._command_handle(command, object_type)
            item = await layout_handle.layout.visual_item()
            layout_str = item.text
        else:
            layout_str = ''
        return Item(
            id=command.id,
            code_id=command.code_id,
            kind=kind,
            path='/'.join(path),
            layout=layout_str,
            )

    async def _command_handle(self, command, object_type):
        return (await self._layout_handle.command_handle(command.id, object_type))

    async def _run_command(self, command_id):
        command = self._id_to_layout_command[command_id]
        command = command.with_(layout_handle=self._layout_handle)
        resolved_piece = await command.run()
        return resolved_piece

    @command('run', kind='element')
    async def _run(self, item_key):
        command_id = item_key
        return (await self._run_command(command_id))

    @object_command('layout', kind='element')
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

    @object_command('add', kind='element')
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

    @command('_add_command_impl')
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


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)

        command_list_type = htypes.command_list.command_list_object_type(
            command_list=(
                htypes.object_type.object_command('run', None),
                htypes.object_type.object_command('layout', None),
                htypes.object_type.object_command('add', None),
                ),
            )
        CommandList.type = command_list_type

        services.object_registry.register_actor(
            htypes.command_list.command_list,
            CommandList.from_state,
            services.mosaic,
            services.async_web,
            services.object_registry,
            services.object_layout_association,
            services.layout_handle_from_ref,
            services.layout_handle_from_object_type,
            )
