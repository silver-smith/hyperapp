import itertools
from collections import namedtuple

from hyperapp.common.util import single
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule

from . import htypes
from .column import Column
from .object_command import command as object_command
from .layout import LayoutWatcher
from .simple_list_object import SimpleListObject


Item = namedtuple('Item', 'path id code_id kind layout')


class CommandList(SimpleListObject):

    @classmethod
    async def from_state(cls, state, ref_registry, async_ref_resolver, object_registry, layout_handle_resolver):
        piece = await async_ref_resolver.resolve_ref_to_object(state.piece_ref)
        object = await object_registry.resolve_async(piece)
        layout_handle = await layout_handle_resolver.resolve(state.layout_handle_ref, object)
        return cls(ref_registry, object, layout_handle)

    def __init__(self, ref_registry, object, layout_handle):
        super().__init__()
        self._ref_registry = ref_registry
        self._object = object
        self._layout_handle = layout_handle

    @property
    def title(self):
        return f"Commands for: {self._layout_handle.title}"

    @property
    def data(self):
        piece_ref = self._ref_registry.register_object(self._object.data)
        layout_handle_ref = self._ref_registry.register_object(self._layout_handle.data)
        return htypes.command_list.command_list(piece_ref, layout_handle_ref)

    @property
    def columns(self):
        return [
            Column('path'),
            Column('id', is_key=True),
            Column('code_id'),
            Column('kind'),
            Column('layout'),
            ]

    async def get_all_items(self):
        return [
            await self._make_item(command)
            for command in self._layout.command_list
            ]

    @property
    def _layout(self):
        return self._layout_handle.layout

    async def _make_item(self, command):
        resolved_piece = await self._run_command(command)
        if resolved_piece is not None:
            item = await resolved_piece.layout_handle.layout.visual_item()
            layout_str = item.text
        else:
            layout_str = ''
        return Item(
            path='/' + '/'.join(command.path),
            id=command.id,
            code_id=command.code_command.id,
            kind=command.code_command.kind,
            layout=layout_str,
            )

    async def _run_command(self, command):
        if command.kind == 'element':
            key = await self._object.first_item_key()
            args = [key]
        else:
            args = []
        resolved_piece = await command.run(*args)
        return resolved_piece

    def _command_by_id(self, command_id):
        return single(
            command for command in self._layout.command_list
            if command.id == command_id
            )

    @command('run', kind='element')
    async def _run(self, item_key):
        # todo: pass current item to command list, use it here for element commands.
        command = self._command_by_id(item_key)
        return (await self._run_command(command))

    @object_command('layout', kind='element')
    async def _open_layout(self, item_key):
        command = self._command_by_id(item_key)
        resolved_piece = await self._run_command(command)
        if resolved_piece is None:
            return None
        piece_ref = self._ref_registry.register_object(resolved_piece.object.data)
        layout_ref = self._ref_registry.register_object(resolved_piece.layout.data)
        category = self._object.category_list[-1]
        return htypes.layout_editor.object_layout_editor(piece_ref, layout_ref, category, command.id)

    @object_command('add', kind='element')
    async def _add_command(self, path):
        piece_ref = self._ref_registry.register_object(self._object.data)
        layout_ref = self._ref_registry.register_object(self._layout.data)
        chooser = htypes.code_command_chooser.code_command_chooser(piece_ref, layout_ref)
        chooser_ref = self._ref_registry.register_object(chooser)
        code_command_id_field = htypes.params_editor.field('code_command_id', chooser_ref)
        return htypes.params_editor.params_editor(
            target_piece_ref=self._ref_registry.register_object(self.data),
            target_command_id=self._add_command_impl.id,
            bound_arguments=[],
            fields=[code_command_id_field],
            )

    @command('_add_command_impl')
    async def _add_command_impl(self, code_command_id):
        new_code_command_id = self._make_command_id_unique(code_command_id)
        command = self._layout.add_command(new_code_command_id, code_command_id)
        return self.data

    def _make_command_id_unique(self, command_id):
        if not self._command_id_exists(command_id):
            return command_id
        for idx in itertools.count():
            unique_id = f'{command_id}_{idx}'
            if not self._command_id_exists(unique_id):
                return unique_id

    def _command_id_exists(self, command_id):
        for command in self._layout.command_list:
            if command.id == command_id:
                return True
        return False


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_type(
            htypes.command_list.command_list,
            CommandList.from_state,
            services.ref_registry,
            services.async_ref_resolver,
            services.object_registry,
            services.layout_handle_resolver,
            )
