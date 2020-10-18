import itertools
from collections import namedtuple

from hyperapp.common.util import single
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .column import Column
from .object_command import command as object_command
from .layout_handle import LayoutWatcher
from .simple_list_object import SimpleListObject


Item = namedtuple('Item', 'id code_id kind path layout')


class CommandList(SimpleListObject):

    @classmethod
    async def from_state(cls, state, ref_registry, async_ref_resolver, object_registry, layout_handle_from_ref, layout_handle_from_object_type):
        piece = await async_ref_resolver.resolve_ref_to_piece(state.piece_ref)
        object = await object_registry.animate(piece)
        layout_handle = await layout_handle_from_ref(state.layout_handle_ref)
        self = cls(ref_registry, layout_handle_from_object_type, object, layout_handle)
        await self._async_init(async_ref_resolver)
        return self

    def __init__(self, ref_registry, layout_handle_from_object_type, object, layout_handle):
        super().__init__()
        self._ref_registry = ref_registry
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

    async def _async_init(self, async_ref_resolver):
        self._command_object_types = {
            command.id: await async_ref_resolver.resolve_ref_to_piece(command.result_object_type_ref)
            for command in self._object.type.command_list
            }
        # todo: add/pass current item to command list constructor/data, use it here.
        self._item_key = await self._object.first_item_key()
        self._id_to_layout_command = {
            command.id: command
            for command in self._layout.get_item_commands(self._object, self._item_key)
            }

    @property
    def title(self):
        return f"Commands for: {self._layout_handle.title}"

    @property
    def data(self):
        piece_ref = self._ref_registry.distil(self._object.data)
        layout_handle_ref = self._ref_registry.distil(self._layout_handle.data)
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
        object_type = self._command_object_types[command.id]
        if object_type is not None:
            layout_handle = await self._command_handle(command, object_type)
            item = await layout_handle.layout.visual_item()
            layout_str = item.text
        else:
            layout_str = ''
        if command.code_id:
            path, code_command = self._id_to_path_and_code_command[command.code_id]
            kind = code_command.kind
        else:
            path = []
            kind = ''
        return Item(
            id=command.id,
            code_id=command.code_id,
            kind=kind,
            path='/'.join(path),
            layout=layout_str,
            )

    async def _command_handle(self, command, object_type):
        return (await self._layout_handle.command_handle(command.id, object_type, command.layout_ref))

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
        object_type = self._command_object_types[command_id]
        if object_type is None:
            # Associating layout to dynamic-object-type command is forbidden. Even if we can run command to get it.
            return None
        command_handle = await self._command_handle(self._command_dict[command_id], object_type)
        layout_handle_ref = self._ref_registry.distil(command_handle.data)
        return htypes.layout_editor.object_layout_editor(layout_handle_ref)

    @object_command('add', kind='element')
    async def _add_command(self, path):
        piece_ref = self._ref_registry.distil(self._object.data)
        layout_ref = self._ref_registry.distil(self._layout.data)
        chooser = htypes.code_command_chooser.code_command_chooser(piece_ref, layout_ref)
        chooser_ref = self._ref_registry.distil(chooser)
        code_command_id_field = htypes.params_editor.field('code_command_id', chooser_ref)
        return htypes.params_editor.params_editor(
            target_piece_ref=self._ref_registry.distil(self.data),
            target_command_id=self._add_command_impl.id,
            bound_arguments=[],
            fields=[code_command_id_field],
            )

    @command('_add_command_impl')
    async def _add_command_impl(self, code_command_id):
        new_code_command_id = self._make_command_id_unique(code_command_id)
        command = self._layout.add_command(new_code_command_id, code_command_id)
        self._command_dict[command.id] = command
        return self.data

    def _make_command_id_unique(self, command_id):
        if command_id not in self._command_dict:
            return command_id
        for idx in itertools.count():
            unique_id = f'{command_id}_{idx}'
            if unique_id not in self._command_dict:
                return unique_id


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
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
            services.ref_registry,
            services.async_ref_resolver,
            services.object_registry,
            services.layout_handle_from_ref,
            services.layout_handle_from_object_type,
            )
